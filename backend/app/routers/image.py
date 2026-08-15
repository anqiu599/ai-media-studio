from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os

from app.services.image_service import process_image, process_image_all_styles
from app.services.style_presets import IMAGE_STYLES
from app.utils.file_utils import save_upload, cleanup_temp_files
from app.config import OUTPUT_DIR

router = APIRouter(prefix="/api/image", tags=["image"])


@router.get("/styles")
async def get_styles():
    """Get available image styles."""
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
async def process_image_endpoint(
    file: UploadFile = File(...),
    style: str = Form("all"),
):
    """Upload an image and process it with specified style(s)."""
    # Validate by extension (more reliable than MIME on Windows)
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported format: {ext}. Supported: {', '.join(sorted(allowed_ext))}")

    # Save uploaded file
    filepath = await save_upload(file, "img_")

    try:
        if style == "all":
            results = await process_image_all_styles(filepath)
        elif style in IMAGE_STYLES:
            results = [await process_image(filepath, style)]
        else:
            raise HTTPException(400, f"Unknown style: {style}. Available: {list(IMAGE_STYLES.keys())}")

        # Filter errors
        errors = [r for r in results if "error" in r]
        successes = [r for r in results if "error" not in r]

        return {
            "total_styles": len(results),
            "success_count": len(successes),
            "error_count": len(errors),
            "results": successes,
            "errors": errors if errors else None,
        }

    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        # Upload file is no longer needed once processing is done
        cleanup_temp_files(filepath)


@router.get("/download/{filename}")
async def download_image(filename: str):
    """Download a processed image."""
    filepath = os.path.join(OUTPUT_DIR, "images", filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, f"File not found: {filename}")
    return FileResponse(filepath, media_type="image/jpeg", filename=filename)
