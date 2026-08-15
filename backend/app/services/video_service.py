"""Video processing service.

Pipeline:
  video → OpenCV (decode + optional trim) → per-frame style preset + AI tuning
       → temp MPEG-4 (cv2.VideoWriter) → ffmpeg → H.264 (browser-playable)
       → optional audio copy (trimmed) → mux → final MP4

All ffmpeg subprocesses use file-based arguments only (no piped stdio), so the
service works even under restrictive sandboxes. Progress is tracked in an
in-memory job store and polled by the frontend.
"""

import os
import subprocess
import threading
import time
import uuid

import cv2
import numpy as np
from PIL import Image

from app.config import OUTPUT_DIR
from app.services.ai_service import ai_service
from app.services.style_presets import IMAGE_STYLES
from app.utils import cv_analysis, image_filters
from app.utils.file_utils import get_output_path

VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)

# job_id -> {status, progress(0-100), message, result, error}
JOBS: dict[str, dict] = {}

QUALITY_SCALES = {
    "original": 0.0,  # 0.0 = keep source resolution
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
}

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def _run_ffmpeg(args: list[str]):
    """Run ffmpeg with file-based args; raises CalledProcessError on failure."""
    subprocess.run(
        [FFMPEG, "-y", *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _probe_has_audio(path: str) -> bool:
    """Detect whether a media file has an audio stream (no stdout pipes)."""
    probe_file = os.path.join(VIDEO_DIR, f"_probe_{uuid.uuid4().hex[:8]}.txt")
    try:
        subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0",
             "-o", probe_file, path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if os.path.exists(probe_file):
            with open(probe_file, "r", encoding="utf-8", errors="ignore") as f:
                return any(line.strip() for line in f)
        return False
    except Exception:
        return False
    finally:
        try:
            if os.path.exists(probe_file):
                os.remove(probe_file)
        except OSError:
            pass


def create_job(job_id: str) -> None:
    JOBS[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "排队中...",
        "result": None,
        "error": None,
    }


def get_job(job_id: str) -> dict | None:
    return JOBS.get(job_id)


def _update(job_id: str, **kwargs) -> None:
    job = JOBS.get(job_id)
    if job:
        job.update(kwargs)


async def _ai_tune_for_video(style: dict, sample_frame_path: str) -> dict:
    """Run one CV analysis + one DeepSeek call on a representative frame."""
    try:
        cv_data = cv_analysis.analyze_image_cv(sample_frame_path)
        description = cv_analysis.generate_image_description_cv(cv_data)
        result = await ai_service.generate_filter_params(description, style)
        return result.get("params") or style.get("params", {})
    except Exception:
        return style.get("params", {})


def process_video(
    input_path: str,
    style_key: str,
    start_sec: float = 0.0,
    end_sec: float = 0.0,
    quality: str = "720p",
    job_id: str = "job",
) -> dict:
    """
    Apply a style preset to every frame of the video within [start_sec, end_sec].
    Returns {output_filename, duration, frames, fps, width, height, ...}.
    """
    style = IMAGE_STYLES.get(style_key)
    if not style:
        raise ValueError(f"未知风格: {style_key}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("无法读取视频文件，请确认格式为 MP4/MOV/AVI/WebM")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    if fps <= 0 or fps > 240:
        fps = 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if w <= 0 or h <= 0:
        cap.release()
        raise ValueError("无法读取视频尺寸")

    duration = total_frames / fps if total_frames > 0 else 0.0

    # Trim window (0 or negative end = till the end)
    start = max(0.0, float(start_sec or 0.0))
    end = min(duration, float(end_sec)) if end_sec and float(end_sec) > start else duration
    if end <= start:
        end = duration
    start_frame = int(round(start * fps))
    end_frame = min(total_frames, int(round(end * fps))) if total_frames else int(round(end * fps))
    if end_frame <= start_frame:
        end_frame = start_frame + 1
    out_frames = end_frame - start_frame

    # Resolution scale
    max_dim = QUALITY_SCALES.get(quality, 720)
    scale = 1.0
    if max_dim and max_dim > 0:
        scale = min(1.0, max_dim / max(w, h))
    out_w = max(2, int(w * scale) // 2 * 2)
    out_h = max(2, int(h * scale) // 2 * 2)

    _update(job_id, status="processing", progress=2, message=f"正在分析视频（{w}x{h}，{duration:.1f}s）...")

    # AI tuning on a representative middle frame (once per job, not per frame)
    ai_params = {}
    mid_frame = start_frame + out_frames // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
    ok, sample = cap.read()
    if ok:
        sample_path = os.path.join(VIDEO_DIR, f"_sample_{job_id}.jpg")
        try:
            cv2.imwrite(sample_path, sample)
            import asyncio

            ai_params = asyncio.run(_ai_tune_for_video(style, sample_path))
        except Exception:
            ai_params = {}
        finally:
            try:
                if os.path.exists(sample_path):
                    os.remove(sample_path)
            except OSError:
                pass
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    preset_func = image_filters.FILTER_FUNCTIONS.get(style["filter_func"]) or image_filters.apply_natural_preset

    # ---- Pass 1: decode + filter + write temp MPEG-4 ----
    temp_raw = os.path.join(VIDEO_DIR, f"_{job_id}_raw.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(temp_raw, fourcc, fps, (out_w, out_h))
    if not writer.isOpened():
        cap.release()
        raise ValueError("无法创建输出视频（编码器初始化失败）")

    _update(job_id, progress=5, message=f"渲染中（{style['name']}）...")
    idx = 0
    t0 = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx >= out_frames:
            break
        if out_w != w or out_h != h:
            frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_AREA)
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        pil = preset_func(pil)
        pil = image_filters.apply_ai_tuning(pil, ai_params)
        frame_out = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        writer.write(frame_out)
        idx += 1
        if idx % 10 == 0 or idx == out_frames:
            pct = 5 + int(idx / max(out_frames, 1) * 70)
            elapsed = time.time() - t0
            speed = idx / max(elapsed, 0.01)
            eta = (out_frames - idx) / max(speed, 0.01)
            _update(job_id, progress=pct, message=f"渲染帧 {idx}/{out_frames}（约剩 {eta:.0f}s）")

    writer.release()
    cap.release()
    if idx == 0:
        try:
            os.remove(temp_raw)
        except OSError:
            pass
        raise ValueError("没有可处理的帧，请检查裁剪范围")

    # ---- Pass 2: transcode to H.264 (browser-playable) ----
    _update(job_id, progress=80, message="正在编码 H.264...")
    temp_h264 = os.path.join(VIDEO_DIR, f"_{job_id}_h264.mp4")
    _run_ffmpeg([
        "-i", temp_raw,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        temp_h264,
    ])

    # ---- Pass 3: audio (trimmed) + mux ----
    final_name = f"{job_id}.mp4"
    final_path = get_output_path(final_name, "videos")
    has_audio = _probe_has_audio(input_path)

    if has_audio:
        _update(job_id, progress=90, message="合成音轨...")
        temp_audio = os.path.join(VIDEO_DIR, f"_{job_id}_audio.m4a")
        _run_ffmpeg([
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
            "-i", input_path,
            "-vn", "-c:a", "aac", "-b:a", "128k",
            temp_audio,
        ])
        _run_ffmpeg([
            "-i", temp_h264, "-i", temp_audio,
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", "-movflags", "+faststart",
            final_path,
        ])
        try:
            os.remove(temp_audio)
        except OSError:
            pass
    else:
        os.replace(temp_h264, final_path)

    for p in (temp_raw, temp_h264):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass

    return {
        "output_filename": final_name,
        "style_key": style_key,
        "style_name": style["name"],
        "duration": round(end - start, 2),
        "frames": idx,
        "fps": round(fps, 2),
        "width": out_w,
        "height": out_h,
        "has_audio": has_audio,
    }


def run_job(job_id: str, input_path: str, style_key: str,
            start_sec: float, end_sec: float, quality: str) -> None:
    """Background worker: runs process_video and stores the outcome in JOBS."""
    try:
        result = process_video(input_path, style_key, start_sec, end_sec, quality, job_id=job_id)
        _update(job_id, status="done", progress=100, message="处理完成", result=result)
    except Exception as e:
        _update(job_id, status="error", message=str(e), error=str(e))
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except OSError:
            pass
