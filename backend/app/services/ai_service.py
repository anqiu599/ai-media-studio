"""AI service - Uses DeepSeek for text reasoning + OpenCV for image analysis.

Architecture:
  Image/Frame → OpenCV(CV analysis → numerical data) → DeepSeek(reason over data → decisions)
  No vision API required. Works with DeepSeek API only.

If DEEPSEEK_API_KEY is missing or invalid, every method degrades gracefully to
the style's default parameters so the app keeps working without AI.
"""

import base64
import json
import os
from typing import Optional

from openai import OpenAI

import app.config as config
from app.services.style_presets import IMAGE_STYLES
from app.utils import cv_analysis

# Prompt for tuning a single style
_TUNE_SCHEMA = (
    '{"analysis":"一句话说明(30字内)","params":{"brightness":1.0,"contrast":1.0,'
    '"saturation":1.0,"sharpness":1.0}}'
)

_TUNE_RULES = (
    "参数范围：brightness 0.85-1.25、contrast 0.85-1.35、saturation 0.80-1.40、"
    "sharpness 1.00-1.30（1.0 表示不调整）。"
    "根据图片实际状态微调：偏暗→提亮、过曝→压暗、灰蒙蒙/低对比→增强对比、"
    "色彩平淡→提高饱和、色彩过艳→降低饱和、模糊→轻微锐化、检测到人脸→整体柔和。"
    "所有数值相对原图的比例，必须落在上述范围内。"
)


class AIService:
    """AI service that uses OpenCV for image understanding and DeepSeek for reasoning."""

    def __init__(self):
        # DeepSeek client for text reasoning (the only API needed)
        key = (config.DEEPSEEK_API_KEY or "").strip()
        self.has_key = bool(key) and key not in ("sk-your-deepseek-key-here", "sk-your-api-key-here")
        self.deepseek = OpenAI(
            api_key=key or "missing",
            base_url=config.DEEPSEEK_BASE_URL,
        )
        self.deepseek_model = config.DEEPSEEK_MODEL

        # Optional vision model for richer descriptions (if configured)
        self.has_vision = bool(config.VISION_API_KEY and config.VISION_API_KEY != "sk-your-vision-api-key-here" and config.VISION_API_KEY != "ollama")
        self._vision_client = None

        if self.has_vision or config.VISION_PROVIDER == "ollama":
            self._init_vision()

    def _init_vision(self):
        """Initialize optional vision model client."""
        try:
            if config.VISION_PROVIDER == "ollama":
                self._vision_client = OpenAI(
                    api_key="ollama",
                    base_url=config.VISION_BASE_URL,
                )
            else:
                self._vision_client = OpenAI(
                    api_key=config.VISION_API_KEY,
                    base_url=config.VISION_BASE_URL,
                )
        except Exception:
            self._vision_client = None

    # ================================================================
    # Image Analysis (CV-based by default, vision model as enhancement)
    # ================================================================

    def _image_to_base64(self, image_path: str) -> str:
        """Convert an image file to base64 data URL (for optional vision API)."""
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        return f"data:{mime};base64,{data}"

    async def analyze_image(self, image_path: str) -> str:
        """
        Analyze an image and return a text description.
        Uses OpenCV for technical analysis, optionally enhanced by vision model.
        """
        # Always do CV analysis first (free, fast, no API needed)
        cv_data = cv_analysis.analyze_image_cv(image_path)
        cv_description = cv_analysis.generate_image_description_cv(cv_data)

        # If vision model is available, get a richer description and combine
        if self._vision_client:
            try:
                data_url = self._image_to_base64(image_path)
                response = self._vision_client.chat.completions.create(
                    model=config.VISION_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_url}},
                            {"type": "text", "text": "用一句话描述这张图片的内容和氛围（20字以内）"},
                        ]
                    }],
                    max_tokens=100,
                )
                content_desc = response.choices[0].message.content or ""
                return f"[画面内容] {content_desc.strip()}。[技术指标] {cv_description}"
            except Exception:
                pass

        return cv_description

    # ================================================================
    # DeepSeek: Reasoning & Decision Making
    # ================================================================

    def _call_deepseek(self, prompt: str, max_tokens: int = 900) -> Optional[dict]:
        """Call DeepSeek and parse a JSON object response. Returns None on failure."""
        if not self.has_key:
            return None
        for attempt in range(2):
            try:
                response = self.deepseek.chat.completions.create(
                    model=self.deepseek_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                    temperature=0.6,
                    timeout=120,
                )
                return json.loads(response.choices[0].message.content or "{}")
            except Exception:
                if attempt == 1:
                    return None
        return None

    async def generate_filter_params(self, image_description: str, style: dict) -> dict:
        """
        Ask DeepSeek to tune the four standard knobs for ONE style.
        Returns {"analysis": ..., "params": {...}} (defaults on failure).
        """
        prompt = f"""你是专业照片调色师。下面是一张图片的 OpenCV 技术分析数据：
{image_description}

目标风格：{style['name']}（{style['description']}）
默认参数：{json.dumps(style.get('params', {}), ensure_ascii=False)}

{_TUNE_RULES}

请在该风格基调之上微调，返回 JSON 格式：
{_TUNE_SCHEMA}"""

        result = self._call_deepseek(prompt)
        if result is None:
            return {"analysis": "AI 未配置或调用失败，使用默认参数", "params": style.get("params", {})}

        params = result.get("params") or {}
        if not isinstance(params, dict):
            params = style.get("params", {})
        return {
            "analysis": str(result.get("analysis", ""))[:60],
            "params": params,
        }

    async def generate_filter_params_batch(self, image_description: str) -> dict:
        """
        Tune ALL styles in a single DeepSeek call (much faster than N calls).
        Returns {style_key: {"analysis": ..., "params": {...}}} with defaults
        filled in for any style the model skipped.
        """
        style_lines = "\n".join(
            f"- {key} {s['name']}: {s['description']} | 默认 {json.dumps(s.get('params', {}), ensure_ascii=False)}"
            for key, s in IMAGE_STYLES.items()
        )
        prompt = f"""你是专业照片调色师。下面是一张图片的 OpenCV 技术分析数据：
{image_description}

请为以下每种风格输出微调参数（在该风格基调之上，根据图片实际状态调整）：
{style_lines}

{_TUNE_RULES}

返回 JSON 格式（analysis 只需在最外层给出一次）：
{{"analysis":"对整张图的总体判断与调色思路(40字内)",
 "styles":{{
   "{list(IMAGE_STYLES.keys())[0]}":{{"params":{{"brightness":1.0,"contrast":1.0,"saturation":1.0,"sharpness":1.0}}}},
   "...(其余风格同理)"
 }}}}"""

        result = self._call_deepseek(prompt, max_tokens=2200)
        if result is None:
            return {
                key: {"analysis": "AI 未配置或调用失败，使用默认参数", "params": style.get("params", {})}
                for key, style in IMAGE_STYLES.items()
            }

        styles_out = result.get("styles") if isinstance(result.get("styles"), dict) else {}
        overall = str(result.get("analysis", "")).strip()[:80] or "已根据画面光影色彩自动微调参数"
        batch = {}
        for key, style in IMAGE_STYLES.items():
            entry = styles_out.get(key) or {}
            params = entry.get("params") if isinstance(entry, dict) else None
            if not isinstance(params, dict):
                params = style.get("params", {})
            batch[key] = {
                "analysis": overall,
                "params": params,
            }
        return batch


# Singleton instance
ai_service = AIService()
