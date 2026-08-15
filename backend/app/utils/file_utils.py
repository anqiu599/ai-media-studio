import os
import uuid
import aiofiles
from fastapi import UploadFile

from app.config import UPLOAD_DIR, OUTPUT_DIR


def generate_filename(original_name: str, prefix: str = "") -> str:
    """Generate a unique filename preserving extension."""
    ext = os.path.splitext(original_name)[1].lower()
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}{unique_id}{ext}"


async def save_upload(file: UploadFile, prefix: str = "") -> str:
    """Save an uploaded file and return the file path."""
    filename = generate_filename(file.filename or "file", prefix)
    filepath = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)
    return filepath


def get_output_path(filename: str, subdir: str = "") -> str:
    """Get a path in the output directory."""
    if subdir:
        d = os.path.join(OUTPUT_DIR, subdir)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, filename)
    return os.path.join(OUTPUT_DIR, filename)


def cleanup_temp_files(*paths: str):
    """Remove temporary files."""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
