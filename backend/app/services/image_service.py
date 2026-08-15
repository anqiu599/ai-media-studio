"""Image processing service - orchestrates AI analysis + filter application."""

import os

from PIL import Image

from app.services.ai_service import ai_service
from app.services.style_presets import IMAGE_STYLES
from app.utils.file_utils import get_output_path
from app.utils import image_filters

# Maximum working dimension while filtering (large photos get downscaled
# for speed, then upscaled back to the original size for output).
MAX_WORK_DIM = 2560


def _open_resized(image_path: str) -> tuple[Image.Image, tuple[int, int]]:
    """Open an image, returning (working_image, original_size)."""
    img = Image.open(image_path).convert("RGB")
    original_size = img.size
    w, h = original_size
    if max(w, h) > MAX_WORK_DIM:
        scale = MAX_WORK_DIM / max(w, h)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return img, original_size


def _save_result(img: Image.Image, original_size: tuple[int, int], output_path: str):
    """Restore original dimensions (if downscaled) and save."""
    if img.size != original_size:
        img = img.resize(original_size, Image.LANCZOS)
    img.save(output_path, quality=92)


async def _process_with_params(image_path: str, style_key: str, ai_result: dict) -> dict:
    """Apply one style to an image using a precomputed AI result."""
    style = IMAGE_STYLES[style_key]
    img, original_size = _open_resized(image_path)

    filter_func = image_filters.FILTER_FUNCTIONS.get(style["filter_func"])
    if filter_func:
        processed = filter_func(img)
    else:
        processed = img

    # The AI-tuned deltas actually take effect here:
    processed = image_filters.apply_ai_tuning(processed, ai_result.get("params") or {})

    basename = os.path.basename(image_path)
    name, ext = os.path.splitext(basename)
    output_filename = f"{name}_{style_key}{ext}"
    output_path = get_output_path(output_filename, "images")
    _save_result(processed, original_size, output_path)

    return {
        "style_key": style_key,
        "style_name": style["name"],
        "style_icon": style["icon"],
        "description": ai_result.get("description", ""),
        "ai_analysis": ai_result.get("analysis", ""),
        "output_path": output_path,
        "output_filename": output_filename,
    }


async def process_image(image_path: str, style_key: str) -> dict:
    """
    Process an image with the specified style (single style, full AI pipeline).
    1. AI analyzes the image (OpenCV + optional vision)
    2. AI tunes filter parameters for the style
    3. Apply the preset + tuned parameters
    4. Save and return the result
    """
    if style_key not in IMAGE_STYLES:
        return {"error": f"Unknown style: {style_key}", "available": list(IMAGE_STYLES.keys())}

    try:
        description = await ai_service.analyze_image(image_path)
        ai_result = await ai_service.generate_filter_params(description, IMAGE_STYLES[style_key])
        ai_result["description"] = description
        return await _process_with_params(image_path, style_key, ai_result)
    except Exception as e:
        return {"error": str(e), "style_key": style_key}


async def process_image_all_styles(image_path: str, style_keys: list[str] = None) -> list[dict]:
    """
    Process an image with all (or specified) styles.
    Uses ONE DeepSeek call for all styles (batch tuning) instead of N calls.
    """
    if style_keys is None:
        style_keys = list(IMAGE_STYLES.keys())

    results = []
    try:
        description = await ai_service.analyze_image(image_path)
        batch = await ai_service.generate_filter_params_batch(description)
        for key in style_keys:
            if key not in IMAGE_STYLES:
                results.append({"error": f"Unknown style: {key}", "style_key": key})
                continue
            ai_result = dict(batch.get(key) or {})
            ai_result["description"] = description
            try:
                results.append(await _process_with_params(image_path, key, ai_result))
            except Exception as e:
                results.append({"error": str(e), "style_key": key})
    except Exception as e:
        # If analysis itself fails, still render every style with defaults
        for key in style_keys:
            ai_result = {"analysis": f"分析失败：{e}", "params": IMAGE_STYLES.get(key, {}).get("params", {})}
            try:
                results.append(await _process_with_params(image_path, key, ai_result))
            except Exception as e2:
                results.append({"error": str(e2), "style_key": key})

    return results
