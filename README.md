# 🎨 AI 影像工坊

AI 驱动的图片美化与视频风格化工具 —— 上传照片或视频，一键生成 9 种电影级风格。

## ✨ 功能

### 🖼️ 图片美化
| 风格 | 效果 |
|------|------|
| 🌿 自然清新 | 微调曝光、自然饱和度、轻微锐化 |
| 📷 复古胶片 | 暖调、颗粒、暗角、褪色，模拟胶片质感 |
| ⚫ 高级黑白 | 强对比灰度与颗粒，突出光影结构 |
| 🌆 赛博朋克 | 紫青霓虹、色彩分离、暗角，赛博都市夜景 |
| 🎐 日系清新 | 过曝柔光、青色调、低对比，日系空气感 |
| 🎬 电影感 | 青橙调色与 S 曲线，好莱坞电影质感 |
| 🏺 莫兰迪 | 低饱和、低对比的高级灰，温柔静谧 |
| 📼 港风复古 | 金绿调、重颗粒与褪色，王家卫式港片氛围 |
| 🌈 鲜艳活力 | 高饱和、明亮通透，让色彩鲜活起来 |

> 每张风格图支持**拖动滑块前后对比**，AI 针对每张照片微调参数。

### 🎬 视频风格化
- 整段视频**逐帧应用**风格滤镜（9 种风格通用）
- **起止裁剪**：拖动时间轴选取任意片段
- **清晰度选择**：原画质 / 1080P / 720P / 480P
- H.264 编码 + `faststart`，浏览器直接播放
- **保留原声**（裁剪后自动对齐音轨）
- **实时进度**：任务队列 + 轮询，显示渲染帧数与剩余时间

## 🏗️ 技术架构

```
上传素材 → OpenCV(提取技术指标) → DeepSeek(推理决策) → Pillow/OpenCV(执行滤镜) → ffmpeg(视频编码) → 输出
```

| 层 | 技术 |
|----|------|
| 前端 | React 19 + Vite + TailwindCSS 4 |
| 后端 | Python FastAPI |
| AI | DeepSeek（批量调参：9 种风格仅需 1 次调用） |
| 视觉分析 | OpenCV（免费，无需额外 API） |
| 图片处理 | Pillow + NumPy |
| 视频处理 | OpenCV 逐帧 + 系统 ffmpeg（H.264） |

> **只需 DeepSeek API** — OpenCV 自动完成亮度/色彩/对比度/人脸等 12 项分析，无需任何视觉 API。

## 🚀 快速开始

### 前置要求
- Node.js >= 18
- Python >= 3.10
- ffmpeg（视频功能需要，`ffmpeg -version` 验证）

### 1. 配置

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
# 未配置时自动降级为默认参数，功能仍可用
```

获取 Key: https://platform.deepseek.com/api_keys

### 2. 启动

```bash
# 终端 1 — 后端
cd backend
py -m uvicorn app.main:app --port 8000

# 终端 2 — 前端
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

## 📁 项目结构

```
├── frontend/               # React + Vite + TailwindCSS
│   └── src/
│       ├── components/     # Layout, StyleSelector, CompareSlider, ImageResultCard...
│       ├── pages/          # HomePage, ImagePage, VideoPage
│       ├── services/       # API 调用
│       └── types/          # TypeScript 类型
├── backend/                # Python FastAPI
│   └── app/
│       ├── main.py         # 入口
│       ├── routers/        # image.py + video.py
│       ├── services/       # AI 服务 + 图片/视频处理 + 风格预设
│       └── utils/          # CV 分析 + 滤镜引擎
└── README.md
```

## 📄 License

MIT
