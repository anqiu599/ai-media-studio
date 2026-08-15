"""AI Image Studio - FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import image, video

app = FastAPI(
    title="AI Image Studio",
    description="AI-powered image beautification with multiple style presets",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image.router)
app.include_router(video.router)


@app.get("/")
async def root():
    return {
        "name": "AI Image Studio",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "image_styles": "/api/image/styles",
            "image_process": "/api/image/process",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
