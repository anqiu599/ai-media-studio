"""
Computer Vision analysis using OpenCV.
Replaces the need for a vision API — extracts technical characteristics
from images so DeepSeek can reason over numerical data instead of natural language.
"""

import cv2
import numpy as np
from typing import Optional


def _imread(path: str) -> np.ndarray | None:
    """Unicode-safe image reading for Windows paths containing CJK characters."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def analyze_image_cv(image_path: str) -> dict:
    """
    Analyze an image using OpenCV and return technical characteristics.
    This completely replaces the vision model for image understanding.
    """
    img = _imread(image_path)
    if img is None:
        return {"error": "Cannot read image"}

    h, w = img.shape[:2]

    # ---- Brightness ----
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))
    # Classify: very dark (<60), dark (60-100), normal (100-170), bright (170-210), very bright (>210)
    if mean_brightness < 60:
        brightness_level = "极暗"
    elif mean_brightness < 100:
        brightness_level = "偏暗"
    elif mean_brightness < 170:
        brightness_level = "正常"
    elif mean_brightness < 210:
        brightness_level = "偏亮"
    else:
        brightness_level = "过曝"

    # ---- Contrast ----
    contrast_std = float(np.std(gray))
    if contrast_std < 25:
        contrast_level = "低对比度/灰蒙蒙"
    elif contrast_std < 55:
        contrast_level = "正常对比度"
    else:
        contrast_level = "高对比度"

    # ---- Color Analysis ----
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Saturation
    mean_saturation = float(np.mean(hsv[:, :, 1]))
    if mean_saturation < 30:
        saturation_level = "色彩黯淡/接近黑白"
    elif mean_saturation < 70:
        saturation_level = "色彩柔和"
    elif mean_saturation < 120:
        saturation_level = "色彩鲜艳"
    else:
        saturation_level = "色彩过饱和"

    # Hue distribution (0-180 in OpenCV)
    hue = hsv[:, :, 0]
    # Red: 0-10 or 160-180
    red_mask = (hue < 10) | (hue > 160)
    red_ratio = float(np.sum(red_mask) / (h * w)) if h * w > 0 else 0
    # Yellow/Orange: 10-35
    yellow_ratio = float(np.sum((hue >= 10) & (hue < 35)) / (h * w)) if h * w > 0 else 0
    # Green: 35-85
    green_ratio = float(np.sum((hue >= 35) & (hue < 85)) / (h * w)) if h * w > 0 else 0
    # Blue/Cyan: 85-135
    blue_ratio = float(np.sum((hue >= 85) & (hue < 135)) / (h * w)) if h * w > 0 else 0
    # Purple/Magenta: 135-160
    purple_ratio = float(np.sum((hue >= 135) & (hue <= 160)) / (h * w)) if h * w > 0 else 0

    # Determine dominant color
    colors = [
        ("红色系", red_ratio),
        ("黄橙色系", yellow_ratio),
        ("绿色系", green_ratio),
        ("蓝青色系", blue_ratio),
        ("紫粉色系", purple_ratio),
    ]
    colors.sort(key=lambda x: x[1], reverse=True)
    dominant_color = colors[0][0] if colors[0][1] > 0.2 else "色彩分布均匀"
    color_palette = ", ".join([f"{c}({r:.0%})" for c, r in colors if r > 0.1])

    # Color temperature estimate (warm = red+yellow dominant, cool = blue+purple dominant)
    warm_score = red_ratio + yellow_ratio
    cool_score = blue_ratio + purple_ratio
    if warm_score > cool_score * 1.5:
        color_temperature = "暖色调"
    elif cool_score > warm_score * 1.5:
        color_temperature = "冷色调"
    else:
        color_temperature = "中性色调"

    # ---- Sharpness / Blur Detection ----
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if laplacian_var < 50:
        sharpness_level = "模糊/失焦"
    elif laplacian_var < 150:
        sharpness_level = "一般清晰度"
    else:
        sharpness_level = "非常清晰/锐利"

    # ---- Edge Density (complexity of scene) ----
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / (h * w)) if h * w > 0 else 0
    if edge_density < 0.03:
        complexity = "简单（大面积纯色/天空/墙面）"
    elif edge_density < 0.08:
        complexity = "中等复杂度"
    else:
        complexity = "复杂（细节丰富/纹理多）"

    # ---- Face Detection ----
    face_count = 0
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        face_count = len(faces)
    except Exception:
        pass

    # ---- Exposure balance (backlit detection) ----
    # Divide image into center and periphery
    cy, cx = h // 2, w // 2
    center_region = gray[cy - h//6:cy + h//6, cx - w//6:cx + w//6]
    center_brightness = float(np.mean(center_region)) if center_region.size > 0 else mean_brightness
    border_brightness = (mean_brightness * h * w - center_brightness * center_region.size) / max(h * w - center_region.size, 1)
    if border_brightness > center_brightness * 1.5:
        lighting_type = "逆光（背景亮主体暗）"
    elif center_brightness > border_brightness * 1.3:
        lighting_type = "主体受光良好"
    else:
        lighting_type = "光线均匀"

    # ---- Aspect Ratio ----
    if w / h > 1.6:
        composition = f"宽幅横构图 ({w}x{h})"
    elif w / h < 0.8:
        composition = f"竖构图 ({w}x{h})"
    else:
        composition = f"标准构图 ({w}x{h})"

    return {
        "resolution": f"{w}x{h}",
        "brightness": {"value": round(mean_brightness, 1), "level": brightness_level},
        "contrast": {"value": round(contrast_std, 1), "level": contrast_level},
        "saturation": {"value": round(mean_saturation, 1), "level": saturation_level},
        "color_temperature": color_temperature,
        "dominant_color": dominant_color,
        "color_palette": color_palette if color_palette else "无明显偏向",
        "sharpness": {"value": round(laplacian_var, 1), "level": sharpness_level},
        "complexity": complexity,
        "lighting": lighting_type,
        "composition": composition,
        "has_faces": face_count > 0,
        "face_count": face_count,
    }


def generate_image_description_cv(analysis: dict) -> str:
    """
    Convert CV analysis data into a structured text description
    that DeepSeek can reason over (replaces vision model output).
    """
    if "error" in analysis:
        return "无法分析该图片"

    b = analysis["brightness"]["level"]
    c = analysis["contrast"]["level"]
    s = analysis["saturation"]["level"]
    ct = analysis["color_temperature"]
    dc = analysis["dominant_color"]
    cp = analysis["color_palette"]
    sh = analysis["sharpness"]["level"]
    cx = analysis["complexity"]
    lt = analysis["lighting"]
    cm = analysis["composition"]
    fc = analysis["face_count"]

    desc_parts = [
        f"分辨率{analysis['resolution']}，{cm}",
        f"曝光{b}（均值{analysis['brightness']['value']}），{c}（标准差{analysis['contrast']['value']}）",
        f"色彩{s}（饱和度均值{analysis['saturation']['value']}），{ct}，主色调为{dc}",
    ]
    if cp:
        desc_parts.append(f"色彩构成：{cp}")
    desc_parts.append(f"清晰度{sh}，场景{analysis['complexity']}")
    desc_parts.append(f"光线：{lt}")

    if fc > 0:
        desc_parts.append(f"检测到{fc}张人脸")

    return "；".join(desc_parts)


def analyze_frame_cv(frame_path: str) -> dict:
    """
    Analyze a single video frame using CV.
    Returns frame-level metrics useful for editing decisions.
    """
    img = _imread(frame_path)
    if img is None:
        return {"error": "Cannot read frame"}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Basic metrics
    mean_brightness = float(np.mean(gray))
    contrast_std = float(np.std(gray))
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Motion potential (edge density as proxy for activity)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / (h * w)) if h * w > 0 else 0

    # Color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mean_saturation = float(np.mean(hsv[:, :, 1]))

    # Face detection
    face_count = 0
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        face_count = len(faces)
    except Exception:
        pass

    # Scene change score (will be compared with adjacent frames downstream)
    return {
        "brightness": round(mean_brightness, 1),
        "contrast": round(contrast_std, 1),
        "sharpness": round(laplacian_var, 1),
        "saturation": round(mean_saturation, 1),
        "activity": round(edge_density, 4),  # Higher = more detail/movement in frame
        "faces": face_count,
    }


def generate_frame_description_cv(frame_metrics: dict, time_sec: int,
                                   prev_metrics: Optional[dict] = None) -> str:
    """
    Convert CV frame metrics into a text description for DeepSeek.
    """
    if "error" in frame_metrics:
        return f"[{time_sec}s] 无法读取帧"

    brightness = frame_metrics["brightness"]
    contrast = frame_metrics["contrast"]
    saturation = frame_metrics["saturation"]
    activity = frame_metrics["activity"]
    faces = frame_metrics["faces"]

    # Brightness classification
    if brightness < 60:
        b_desc = "极暗"
    elif brightness < 100:
        b_desc = "偏暗"
    elif brightness < 170:
        b_desc = "亮度适中"
    elif brightness < 210:
        b_desc = "偏亮"
    else:
        b_desc = "过曝"

    # Activity classification
    if activity < 0.02:
        a_desc = "静态/空白场景"
    elif activity < 0.05:
        a_desc = "低动态"
    elif activity < 0.10:
        a_desc = "中等动态"
    else:
        a_desc = "高动态/丰富细节"

    # Scene change vs previous frame
    change_note = ""
    if prev_metrics:
        brightness_diff = abs(brightness - prev_metrics["brightness"])
        activity_diff = abs(activity - prev_metrics["activity"])
        if brightness_diff > 30 or activity_diff > 0.03:
            change_note = " ⚡场景变化"

    parts = [f"[{time_sec}s] {b_desc}，{a_desc}"]

    if saturation < 30:
        parts.append("色彩黯淡")
    elif saturation > 100:
        parts.append("色彩鲜艳")

    if faces > 0:
        parts.append(f"检测到{faces}张人脸")

    if change_note:
        parts.append(change_note)

    return "，".join(parts)
