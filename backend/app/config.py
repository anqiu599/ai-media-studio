import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # deepseek-chat deprecated 2026-07-24

# Vision Model
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "openai")  # openai | anthropic | ollama
VISION_API_KEY = os.getenv("VISION_API_KEY", "")
VISION_BASE_URL = os.getenv("VISION_BASE_URL", "https://api.openai.com/v1")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o-mini")

# Stable Diffusion (optional)
SD_API_KEY = os.getenv("SD_API_KEY", "")
SD_BASE_URL = os.getenv("SD_BASE_URL", "")

# File paths
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
