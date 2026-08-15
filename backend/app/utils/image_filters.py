"""Image filter functions using Pillow, OpenCV and NumPy.

All preset functions accept an optional ``params`` dict (style-specific knobs)
and are intentionally *pure*: they do NOT apply AI tuning. Callers should run
``apply_ai_tuning(img, params)`` *after* a preset so the AI's per-photo
brightness/contrast/saturation/sharpness decisions actually take effect.
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2

# ================================================================
# Basic adjustments
# ================================================================


def apply_brightness(img: Image.Image, factor: float) -> Image.Image:
    """Adjust brightness. factor=1.0 is original, >1 brighter, <1 darker."""
    return ImageEnhance.Brightness(img).enhance(factor)


def apply_contrast(img: Image.Image, factor: float) -> Image.Image:
    """Adjust contrast. factor=1.0 is original."""
    return ImageEnhance.Contrast(img).enhance(factor)


def apply_saturation(img: Image.Image, factor: float) -> Image.Image:
    """Adjust color saturation. factor=1.0 is original, 0 is grayscale."""
    return ImageEnhance.Color(img).enhance(factor)


def apply_sharpness(img: Image.Image, factor: float = 1.2) -> Image.Image:
    """Unsharp-mask sharpening. factor=1.0 is original."""
    if factor <= 1.0:
        return img
    percent = int(round((factor - 1.0) * 150))
    if percent <= 0:
        return img
    return img.filter(ImageFilter.UnsharpMask(radius=2, percent=percent, threshold=3))


# ================================================================
# Color temperature (proper Kelvin white-balance shift)
# ================================================================


def kelvin_to_rgb(kelvin: float) -> tuple[float, float, float]:
    """Approximate a black-body color temperature as (r, g, b) in 0..1."""
    temp = kelvin / 100.0
    if temp <= 66.0:
        red = 255.0
        green = 99.47 * np.log(temp) - 161.12 if temp > 20 else 0.0
        blue = 255.0 if temp <= 19 else 138.52 * np.log(temp - 10) - 305.04
    else:
        red = 329.70 * (temp - 60) ** -0.1332
        green = 288.12 * (temp - 60) ** -0.0755
        blue = 255.0
    r = max(0.0, min(255.0, red)) / 255.0
    g = max(0.0, min(255.0, green)) / 255.0
    b = max(0.0, min(255.0, blue)) / 255.0
    return r, g, b


def apply_temperature(img: Image.Image, temperature: float = 6500) -> Image.Image:
    """
    Shift white balance relative to a 6500K neutral reference.
    temperature < 6500 → warmer (orange/red); > 6500 → cooler (blue).
    """
    r, g, b = kelvin_to_rgb(temperature)
    nr, ng, nb = kelvin_to_rgb(6500)
    arr = np.array(img).astype(np.float32)
    arr[:, :, 0] *= r / nr  # PIL RGB: index 0 = R
    arr[:, :, 1] *= g / ng
    arr[:, :, 2] *= b / nb
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ================================================================
# Tone / film looks
# ================================================================


def apply_tone_curve(img: Image.Image, strength: float = 0.12) -> Image.Image:
    """
    S-curve: darken shadows and brighten highlights while keeping
    black/white endpoints fixed. strength ~0.05 (gentle) .. 0.25 (bold).
    """
    arr = np.array(img).astype(np.float32) / 255.0
    arr = np.clip(arr + strength * np.sin(2 * np.pi * (arr - 0.5)), 0.0, 1.0)
    return Image.fromarray((arr * 255).astype(np.uint8))


def apply_fade(img: Image.Image, amount: float = 0.08) -> Image.Image:
    """Lift blacks toward gray for a faded film look. amount 0..0.2."""
    arr = np.array(img).astype(np.float32) / 255.0
    arr = np.clip(arr * (1 - amount) + amount, 0.0, 1.0)
    return Image.fromarray((arr * 255).astype(np.uint8))


def apply_soft_glow(img: Image.Image, intensity: float = 0.15) -> Image.Image:
    """Screen-blend bloom from a heavy gaussian blur (keeps highlights)."""
    blurred = img.filter(ImageFilter.GaussianBlur(radius=12))
    a = np.array(img).astype(np.float32) / 255.0
    b = np.array(blurred).astype(np.float32) / 255.0
    screen = 1.0 - (1.0 - a) * (1.0 - b)
    out = a * (1.0 - intensity) + screen * intensity
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8))


def apply_vignette(img: Image.Image, strength: float = 0.3) -> Image.Image:
    """Smooth radial darkening toward the corners."""
    w, h = img.size
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2) / np.sqrt(2)
    mask = 1.0 - strength * np.clip(dist, 0, 1) ** 2.2
    arr = np.array(img).astype(np.float32)
    if arr.ndim == 2:
        out = arr * mask
    else:
        out = arr * mask[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def apply_grain(img: Image.Image, intensity: float = 0.05) -> Image.Image:
    """
    Luminance-based film grain: hue-preserving monochrome noise,
    stronger in midtones, gentler in blacks/highlights.
    """
    arr = np.array(img).astype(np.float32)
    if arr.ndim == 2:
        gray = arr
        noise = np.random.normal(0, 255 * intensity, gray.shape)
        lum = gray / 255.0
        out = arr + noise * (0.25 + 0.75 * np.sin(lum * np.pi))
    else:
        gray = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
        noise = np.random.normal(0, 255 * intensity, gray.shape)
        lum = gray / 255.0
        noise *= 0.25 + 0.75 * np.sin(lum * np.pi)  # midtone-weighted
        out = arr + noise[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ================================================================
# Color grading
# ================================================================


def apply_color_split(img: Image.Image, intensity: float = 0.015) -> Image.Image:
    """Chromatic aberration: shift red right, blue left."""
    w, h = img.size
    arr = np.array(img)
    shift = max(1, int(w * intensity))
    result = arr.copy()
    result[:, shift:, 0] = arr[:, : w - shift, 0]
    result[:, : w - shift, 2] = arr[:, shift:, 2]
    return Image.fromarray(result)


def apply_cyan_shift(img: Image.Image, intensity: float = 0.08) -> Image.Image:
    """Shift toward cyan/teal (Japanese light-airy look)."""
    arr = np.array(img).astype(np.float32)
    arr[:, :, 0] *= 1 - intensity * 0.30  # reduce red
    arr[:, :, 1] *= 1 + intensity * 0.10  # slight green
    arr[:, :, 2] *= 1 + intensity * 0.20  # boost blue
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def apply_split_tone(
    img: Image.Image,
    shadow_rgb: tuple[float, float, float] = (0, 0, 0),
    highlight_rgb: tuple[float, float, float] = (0, 0, 0),
    strength: float = 0.2,
) -> Image.Image:
    """
    Blend shadows toward ``shadow_rgb`` and highlights toward ``highlight_rgb``.
    rgb values are 0..255 targets.
    """
    arr = np.array(img).astype(np.float32)
    luma = np.mean(arr, axis=2, keepdims=True) / 255.0
    shadow_mask = (1 - luma) ** 1.5
    highlight_mask = luma**1.5
    for c in range(3):
        arr[:, :, c] += (shadow_rgb[c] - arr[:, :, c]) * shadow_mask[..., 0] * strength
        arr[:, :, c] += (highlight_rgb[c] - arr[:, :, c]) * highlight_mask[..., 0] * strength
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def apply_teal_orange(img: Image.Image, strength: float = 0.28) -> Image.Image:
    """Cinematic teal & orange: shadows toward teal, highlights toward orange."""
    arr = np.array(img).astype(np.float32)
    luma = np.mean(arr, axis=2, keepdims=True) / 255.0
    shadow_mask = 1 - luma
    highlight_mask = luma
    arr[:, :, 0] -= strength * 55 * shadow_mask[..., 0]
    arr[:, :, 1] += strength * 22 * shadow_mask[..., 0]
    arr[:, :, 2] += strength * 30 * shadow_mask[..., 0]
    arr[:, :, 0] += strength * 35 * highlight_mask[..., 0]
    arr[:, :, 2] -= strength * 30 * highlight_mask[..., 0]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def convert_grayscale(img: Image.Image, contrast: float = 1.0) -> Image.Image:
    """Convert to black & white, optionally with extra contrast."""
    gray = ImageOps.grayscale(img)
    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)
    return gray


# ================================================================
# AI tuning — applied AFTER a preset so the AI's decisions matter
# ================================================================

_TUNE_RANGES = {
    "brightness": (0.80, 1.30),
    "contrast": (0.80, 1.40),
    "saturation": (0.70, 1.50),
    "sharpness": (1.00, 1.40),
}


def _clamp(value, lo, hi):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return max(lo, min(hi, v))


def apply_ai_tuning(img: Image.Image, params: dict | None) -> Image.Image:
    """Apply AI-tuned brightness/contrast/saturation/sharpness deltas."""
    if not params:
        return img
    brightness = _clamp(params.get("brightness", 1.0), *_TUNE_RANGES["brightness"])
    contrast = _clamp(params.get("contrast", 1.0), *_TUNE_RANGES["contrast"])
    saturation = _clamp(params.get("saturation", 1.0), *_TUNE_RANGES["saturation"])
    sharpness = _clamp(params.get("sharpness", 1.0), *_TUNE_RANGES["sharpness"])
    if brightness != 1.0:
        img = apply_brightness(img, brightness)
    if contrast != 1.0:
        img = apply_contrast(img, contrast)
    if saturation != 1.0:
        img = apply_saturation(img, saturation)
    if sharpness and sharpness != 1.0:
        img = apply_sharpness(img, sharpness)
    return img


# ================================================================
# Style presets (each accepts optional style-specific params)
# ================================================================


def apply_natural_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """自然清新 — natural light retouch."""
    img = apply_brightness(img, 1.04)
    img = apply_contrast(img, 0.97)
    img = apply_saturation(img, 1.08)
    img = apply_sharpness(img, 1.15)
    return img


def apply_film_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """复古胶片 — warm film, grain, vignette, lifted blacks."""
    img = apply_temperature(img, 5700)
    img = apply_contrast(img, 1.12)
    img = apply_saturation(img, 0.82)
    img = apply_fade(img, 0.05)
    img = apply_vignette(img, 0.28)
    img = apply_grain(img, 0.035)
    return img


def apply_blackwhite_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """高级黑白 — dramatic monochrome."""
    img = convert_grayscale(img, contrast=1.32)
    img = apply_vignette(img, 0.22)
    img = apply_grain(img, 0.025)
    return img


def apply_cyberpunk_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """赛博朋克 — cool purple/cyan neon grade with chromatic aberration."""
    img = apply_contrast(img, 1.28)
    img = apply_saturation(img, 1.45)
    img = apply_temperature(img, 4700)
    img = apply_split_tone(img, shadow_rgb=(90, 40, 170), highlight_rgb=(0, 200, 255), strength=0.18)
    img = apply_color_split(img, 0.014)
    img = apply_vignette(img, 0.22)
    return img


def apply_japanese_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """日系清新 — overexposed, airy, cyan-tinted soft light."""
    img = apply_brightness(img, 1.18)
    img = apply_contrast(img, 0.88)
    img = apply_saturation(img, 0.92)
    img = apply_cyan_shift(img, 0.06)
    img = apply_soft_glow(img, 0.12)
    img = apply_fade(img, 0.05)
    return img


def apply_cinematic_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """电影感 — teal & orange blockbuster grade with S-curve."""
    img = apply_temperature(img, 6200)
    img = apply_tone_curve(img, 0.14)
    img = apply_teal_orange(img, 0.30)
    img = apply_contrast(img, 1.06)
    img = apply_saturation(img, 0.92)
    img = apply_vignette(img, 0.25)
    return img


def apply_morandi_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """莫兰迪 — muted, low-contrast, elegant desaturated tones."""
    img = apply_temperature(img, 6800)
    img = apply_saturation(img, 0.65)
    img = apply_contrast(img, 0.88)
    img = apply_fade(img, 0.12)
    img = apply_soft_glow(img, 0.06)
    return img


def apply_hongkong_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """港风复古 — warm golden-green, heavy grain, faded (Wong Kar-wai vibes)."""
    img = apply_temperature(img, 5400)
    img = apply_saturation(img, 0.85)
    img = apply_contrast(img, 1.05)
    img = apply_split_tone(
        img,
        shadow_rgb=(58, 78, 42),      # olive-green shadows
        highlight_rgb=(232, 190, 96), # warm yellow highlights
        strength=0.30,
    )
    img = apply_fade(img, 0.12)
    img = apply_vignette(img, 0.20)
    img = apply_grain(img, 0.06)
    return img


def apply_vivid_preset(img: Image.Image, params: dict | None = None) -> Image.Image:
    """鲜艳活力 — punchy, saturated, energetic colors."""
    img = apply_saturation(img, 1.35)
    img = apply_contrast(img, 1.10)
    img = apply_temperature(img, 6200)
    img = apply_sharpness(img, 1.20)
    return img


FILTER_FUNCTIONS = {
    "apply_natural_preset": apply_natural_preset,
    "apply_film_preset": apply_film_preset,
    "apply_blackwhite_preset": apply_blackwhite_preset,
    "apply_cyberpunk_preset": apply_cyberpunk_preset,
    "apply_japanese_preset": apply_japanese_preset,
    "apply_cinematic_preset": apply_cinematic_preset,
    "apply_morandi_preset": apply_morandi_preset,
    "apply_hongkong_preset": apply_hongkong_preset,
    "apply_vivid_preset": apply_vivid_preset,
}
