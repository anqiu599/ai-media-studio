import { Link } from 'react-router-dom'
import {
  IconArrowRight, IconCpu, IconImage, IconPalette, IconVideo,
  IconWand, IconSparkles, IconZap, IconChevronRight,
} from '../components/icons'

const styles = [
  ['🌿', '自然清新'], ['📷', '复古胶片'], ['⚫', '高级黑白'], ['🌆', '赛博朋克'],
  ['🎐', '日系清新'], ['🎬', '电影感'], ['🏺', '莫兰迪'], ['📼', '港风复古'], ['🌈', '鲜艳活力'],
]

const features = [
  {
    icon: IconImage,
    title: '图片美化',
    desc: '上传照片，AI 自动分析构图、光影与色彩，一键生成 9 种电影级风格，支持前后对比预览。',
    to: '/image',
    cta: '开始美化',
    accent: 'from-accent/25 to-accent3/10',
  },
  {
    icon: IconVideo,
    title: '视频风格化',
    desc: '整段视频逐帧应用风格滤镜，支持起止裁剪与清晰度选择，H.264 编码、保留原声、实时进度。',
    to: '/video',
    cta: '剪辑视频',
    accent: 'from-accent2/25 to-accent/10',
  },
  {
    icon: IconCpu,
    title: 'AI 智能调参',
    desc: 'OpenCV 提取亮度、对比、色温、人脸等 12 项技术指标，DeepSeek 针对每张作品微调参数。',
    to: '/image',
    cta: '了解原理',
    accent: 'from-accent3/25 to-accent2/10',
  },
]

const steps = [
  ['上传素材', '图片或视频，拖拽即传，最大 200MB'],
  ['AI 分析调参', 'OpenCV 分析画面，DeepSeek 决策参数'],
  ['一键出片', '批量渲染 9 种风格，对比、下载一步到位'],
]

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* ambient orbs */}
      <div className="pointer-events-none absolute -top-40 -left-40 w-[480px] h-[480px] rounded-full bg-accent/20 blur-3xl animate-glow" />
      <div className="pointer-events-none absolute top-10 -right-40 w-[420px] h-[420px] rounded-full bg-accent2/15 blur-3xl animate-glow" style={{ animationDelay: '1.2s' }} />
      <div className="pointer-events-none absolute top-[520px] left-1/3 w-[420px] h-[420px] rounded-full bg-accent3/10 blur-3xl animate-glow" style={{ animationDelay: '2.4s' }} />

      {/* Hero */}
      <section className="relative mx-auto max-w-6xl px-6 pt-20 pb-14 text-center">
        <div className="animate-fade-up inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass text-[12px] text-text mb-6">
          <IconSparkles size={14} className="text-accent-hover" />
          OpenCV 视觉分析 + DeepSeek AI 调参 · 无需视觉 API
        </div>

        <h1 className="animate-fade-up text-4xl sm:text-6xl font-bold tracking-tight text-text-bright leading-[1.12] [animation-delay:80ms]">
          让照片与视频
          <br />
          <span className="gradient-text">焕然一新</span>
        </h1>
        <p className="animate-fade-up mx-auto mt-5 max-w-xl text-[15px] text-text leading-relaxed [animation-delay:160ms]">
          上传一张照片或一段视频，AI 自动分析画面光影与色彩，
          一键生成 9 种精心调校的电影级风格 —— 自然、胶片、赛博朋克、莫兰迪……
        </p>

        <div className="animate-fade-up mt-9 flex flex-wrap items-center justify-center gap-3 [animation-delay:240ms]">
          <Link
            to="/image"
            className="btn-primary inline-flex items-center gap-2 px-7 py-3 rounded-full text-sm font-semibold text-white"
          >
            <IconImage size={17} />
            美化图片
          </Link>
          <Link
            to="/video"
            className="btn-ghost inline-flex items-center gap-2 px-7 py-3 rounded-full text-sm font-semibold text-text-bright"
          >
            <IconVideo size={17} />
            风格化视频
          </Link>
        </div>

        {/* style showcase */}
        <div className="animate-fade-up mt-12 flex flex-wrap justify-center gap-2 [animation-delay:320ms]">
          {styles.map(([icon, name]) => (
            <span key={name} className="chip inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs text-text">
              <span className="text-sm leading-none">{icon}</span>
              {name}
            </span>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="relative mx-auto max-w-6xl px-6 pb-16">
        <div className="grid md:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <Link
              key={f.title}
              to={f.to}
              className={`animate-fade-up card-hover group rounded-2xl border border-border bg-surface/70 backdrop-blur p-6 [animation-delay:${i * 90 + 100}ms]`}
            >
              <div className={`inline-flex w-11 h-11 rounded-xl bg-gradient-to-br ${f.accent} border border-white/10 items-center justify-center text-accent-hover mb-4 group-hover:scale-110 transition-transform`}>
                <f.icon size={21} />
              </div>
              <h3 className="text-[15px] font-semibold text-text-bright mb-1.5">{f.title}</h3>
              <p className="text-[13px] text-text leading-relaxed mb-4 min-h-[60px]">{f.desc}</p>
              <span className="inline-flex items-center gap-1 text-[13px] font-medium text-accent-hover">
                {f.cta}
                <IconArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="relative mx-auto max-w-6xl px-6 pb-20">
        <div className="rounded-3xl border border-border/70 bg-surface/50 backdrop-blur p-8 sm:p-10">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 text-xs text-accent-hover font-medium mb-2">
              <IconWand size={15} /> 三步出片
            </div>
            <h2 className="text-2xl font-bold text-text-bright tracking-tight">极简工作流</h2>
          </div>
          <div className="grid sm:grid-cols-3 gap-6">
            {steps.map((s, i) => (
              <div key={s[0]} className="relative text-center">
                <div className="mx-auto w-10 h-10 rounded-full bg-gradient-to-br from-accent to-accent2 text-white flex items-center justify-center text-sm font-bold shadow-lg shadow-accent/30">
                  {i + 1}
                </div>
                <div className="mt-3 text-sm font-semibold text-text-bright">{s[0]}</div>
                <div className="mt-1 text-xs text-text-dim leading-relaxed">{s[1]}</div>
                {i < 2 && (
                  <IconChevronRight className="hidden sm:block absolute top-2.5 -right-4 text-border-hover" size={18} />
                )}
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 pt-8 border-t border-border/60">
            <div className="flex items-center gap-2 text-xs text-text">
              <IconZap size={15} className="text-warn" />
              批量渲染 9 种风格仅需一次 AI 调用
            </div>
            <span className="hidden sm:block text-border-hover">·</span>
            <div className="flex items-center gap-2 text-xs text-text">
              <IconPalette size={15} className="text-accent3" />
              全部滤镜本地渲染，照片永不上传第三方
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
