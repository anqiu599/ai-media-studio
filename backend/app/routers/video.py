from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
import threading
import uuid

from app.services.style_presets import IMAGE_STYLES
from app.services import video_service
from app.utils.file_utils import save_upload

router = APIRouter(prefix="/api/video", tags=["video"])

ALLOWED_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
QUALITY_KEYS = set(video_service.QUALITY_SCALES.keys())


@router.get("/styles")
async def get_video_styles():
    """Video styles reuse the image style presets."""
    return {
        style_key: {
            "key": style_key,
            "name": style["name"],
            "description": style["description"],
            "icon": style["icon"],
            "preview": style.get("preview", ["#6366f1", "#a855f7"]),
        }
        for style_key, style in IMAGE_STYLES.items()
    }


@router.post("/process")
async def process_video_endpoint(
    file: UploadFile = File(...),
    style: str = Form("film"),
    start_sec: float = Form(0.0),
    end_sec: float = Form(0.0),
    quality: str = Form("720p"),
):
    """
    Start a video style-transfer job. Returns a job_id immediately;
    poll GET /api/video/status/{job_id} for progress.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"不支持格式 {ext}，支持: {', '.join(sorted(ALLOWED_EXT))}")
    if style not in IMAGE_STYLES:
        raise HTTPException(400, f"未知风格: {style}，可选: {list(IMAGE_STYLES.keys())}")
    if quality not in QUALITY_KEYS:
        raise HTTPException(400, f"未知清晰度: {quality}，可选: {sorted(QUALITY_KEYS)}")
    if start_sec < 0 or end_sec < 0:
        raise HTTPException(400, "裁剪时间不能为负数")

    filepath = await save_upload(file, "vid_")
    job_id = uuid.uuid4().hex[:12]
    video_service.create_job(job_id)

    thread = threading.Thread(
        target=video_service.run_job,
        args=(job_id, filepath, style, start_sec, end_sec, quality),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id}


@router.get("/status/{job_id}")
async def get_video_status(job_id: str):
    """Poll the status of a processing job."""
    job = video_service.get_job(job_id)
    if job is None:
        raise HTTPException(404, f"任务不存在: {job_id}")
    return job


@router.get("/download/{filename}")
async def download_video(filename: str):
    """Download a processed video."""
    filepath = os.path.join(video_service.VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, f"文件不存在: {filename}")
    return FileResponse(filepath, media_type="video/mp4", filename=filename)
