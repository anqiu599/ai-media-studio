"""Image style preset definitions.

Each style carries:
- filter_func: preset function name in app.utils.image_filters.FILTER_FUNCTIONS
- params: default AI-tunable targets (brightness/contrast/saturation/sharpness)
- preview: [start, end] hex colors used by the frontend for style-card gradients
"""

IMAGE_STYLES = {
    "natural": {
        "name": "自然清新",
        "description": "微调曝光、自然饱和度、轻微锐化，还原真实质感",
        "icon": "🌿",
        "filter_func": "apply_natural_preset",
        "preview": ["#4ade80", "#22d3ee"],
        "params": {
            "brightness": 1.04,
            "contrast": 0.97,
            "saturation": 1.08,
            "sharpness": 1.15,
        },
    },
    "film": {
        "name": "复古胶片",
        "description": "暖调、颗粒、暗角与褪色，模拟柯达胶片质感",
        "icon": "📷",
        "filter_func": "apply_film_preset",
        "preview": ["#f59e0b", "#92400e"],
        "params": {
            "brightness": 1.00,
            "contrast": 1.12,
            "saturation": 0.82,
            "sharpness": 1.00,
        },
    },
    "bw": {
        "name": "高级黑白",
        "description": "强对比灰度与颗粒，突出光影结构与戏剧感",
        "icon": "⚫",
        "filter_func": "apply_blackwhite_preset",
        "preview": ["#9ca3af", "#1f2937"],
        "params": {
            "brightness": 1.00,
            "contrast": 1.32,
            "saturation": 0.0,
            "sharpness": 1.10,
        },
    },
    "cyberpunk": {
        "name": "赛博朋克",
        "description": "紫青霓虹、色彩分离与暗角，赛博都市夜景",
        "icon": "🌆",
        "filter_func": "apply_cyberpunk_preset",
        "preview": ["#a855f7", "#22d3ee"],
        "params": {
            "brightness": 1.06,
            "contrast": 1.28,
            "saturation": 1.45,
            "sharpness": 1.05,
        },
    },
    "japanese": {
        "name": "日系清新",
        "description": "过曝柔光、青色调与低对比，日系空气感",
        "icon": "🎐",
        "filter_func": "apply_japanese_preset",
        "preview": ["#7dd3fc", "#e0f2fe"],
        "params": {
            "brightness": 1.18,
            "contrast": 0.88,
            "saturation": 0.92,
            "sharpness": 1.00,
        },
    },
    "cinematic": {
        "name": "电影感",
        "description": "青橙调色与 S 曲线，好莱坞电影质感",
        "icon": "🎬",
        "filter_func": "apply_cinematic_preset",
        "preview": ["#0ea5e9", "#f97316"],
        "params": {
            "brightness": 0.98,
            "contrast": 1.10,
            "saturation": 0.92,
            "sharpness": 1.05,
        },
    },
    "morandi": {
        "name": "莫兰迪",
        "description": "低饱和、低对比的高级灰，温柔静谧",
        "icon": "🏺",
        "filter_func": "apply_morandi_preset",
        "preview": ["#c8bfb2", "#8a7f70"],
        "params": {
            "brightness": 1.02,
            "contrast": 0.88,
            "saturation": 0.65,
            "sharpness": 1.00,
        },
    },
    "hongkong": {
        "name": "港风复古",
        "description": "金绿调、重颗粒与褪色，王家卫式港片氛围",
        "icon": "📼",
        "filter_func": "apply_hongkong_preset",
        "preview": ["#eab308", "#4d7c0f"],
        "params": {
            "brightness": 1.00,
            "contrast": 1.05,
            "saturation": 0.85,
            "sharpness": 1.00,
        },
    },
    "vivid": {
        "name": "鲜艳活力",
        "description": "高饱和、明亮通透，让色彩瞬间鲜活起来",
        "icon": "🌈",
        "filter_func": "apply_vivid_preset",
        "preview": ["#f43f5e", "#8b5cf6"],
        "params": {
            "brightness": 1.05,
            "contrast": 1.10,
            "saturation": 1.35,
            "sharpness": 1.20,
        },
    },
}
