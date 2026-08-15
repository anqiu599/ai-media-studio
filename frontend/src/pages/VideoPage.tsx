import { useCallback, useEffect, useRef, useState } from 'react'
import StyleSelector from '../components/StyleSelector'
import ProcessingStatus from '../components/ProcessingStatus'
import { getVideoStyles, processVideo, getVideoJobStatus, getVideoDownloadUrl } from '../services/api'
import type { StyleInfo, VideoJob, VideoQuality } from '../types'
import { QUALITY_LABELS, VIDEO_QUALITIES } from '../types'
import {
  IconCheck, IconClock, IconDownload, IconPlay, IconRefresh, IconScissors, IconUpload, IconVideo, IconX,
} from '../components/icons'

const MAX_SIZE = 200 * 1024 * 1024

function fmtTime(sec: number): string {
  if (!isFinite(sec) || sec < 0) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function VideoPage() {
  const [styles, setStyles] = useState<Record<string, StyleInfo>>({})
  const [style, setStyle] = useState('film')
  const [file, setFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState('')
  const [duration, setDuration] = useState(0)
  const [start, setStart] = useState(0)
  const [end, setEnd] = useState(0)
  const [quality, setQuality] = useState<VideoQuality>('720p')
  const [drag, setDrag] = useState(false)
  const [job, setJob] = useState<VideoJob | null>(null)
  const [resultUrl, setResultUrl] = useState('')
  const [error, setError] = useState('')
  const videoRef = useRef<HTMLVideoElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const pollTimer = useRef<number | null>(null)

  useEffect(() => {
    getVideoStyles().then(setStyles).catch(console.error)
    return () => {
      if (pollTimer.current) window.clearInterval(pollTimer.current)
    }
  }, [])

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith('video/')) {
      setError('请选择视频文件')
      return
    }
    if (f.size > MAX_SIZE) {
      setError('视频不能超过 200MB')
      return
    }
    setError('')
    setFile(f)
    setJob(null)
    setResultUrl('')
    if (videoUrl) URL.revokeObjectURL(videoUrl)
    const url = URL.createObjectURL(f)
    setVideoUrl(url)
    setStart(0)
    setEnd(0)
    setDuration(0)
  }, [videoUrl])

  const onMetadata = () => {
    const d = videoRef.current?.duration ?? 0
    if (d > 0 && isFinite(d)) {
      setDuration(d)
      setEnd(d)
    }
  }

  const reset = () => {
    if (pollTimer.current) window.clearInterval(pollTimer.current)
    setFile(null)
    setJob(null)
    setResultUrl('')
    setError('')
    setDuration(0)
    if (videoUrl) URL.revokeObjectURL(videoUrl)
    setVideoUrl('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const startProcess = async () => {
    if (!file) return
    setError('')
    setJob({ status: 'queued', progress: 0, message: '提交任务...', result: null, error: null })
    try {
      const { job_id } = await processVideo(file, style, start, end, quality)
      pollTimer.current = window.setInterval(async () => {
        try {
          const st = await getVideoJobStatus(job_id)
          setJob(st)
          if (st.status === 'done' && st.result) {
            if (pollTimer.current) window.clearInterval(pollTimer.current)
            setResultUrl(getVideoDownloadUrl(st.result.output_filename))
          } else if (st.status === 'error') {
            if (pollTimer.current) window.clearInterval(pollTimer.current)
          }
        } catch {
          if (pollTimer.current) window.clearInterval(pollTimer.current)
          setError('获取进度失败，请稍后重试')
        }
      }, 1000)
    } catch (e) {
      setError(e instanceof Error ? e.message : '提交失败')
      setJob(null)
    }
  }

  const busy = job?.status === 'queued' || job?.status === 'processing'
  const done = job?.status === 'done' && job.result
  const styleOpts = Object.fromEntries(
    Object.entries(styles).map(([k, v]) => [k, { ...v, key: k }])
  )

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
      {/* page header */}
      <div className="mb-6 animate-fade-up">
        <div className="inline-flex items-center gap-1.5 text-[11px] text-accent2 font-medium mb-1.5">
          <IconVideo size={13} /> 视频风格化
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-text-bright tracking-tight">AI 视频剪辑</h1>
        <p className="text-xs text-text-dim mt-1">
          整段视频逐帧应用风格滤镜 · 支持裁剪片段 · H.264 编码保留原声 · 实时进度
        </p>
      </div>

      <div className="grid lg:grid-cols-[400px_1fr] gap-6 items-start">
        {/* ============ left: controls ============ */}
        <aside className="lg:sticky lg:top-20 space-y-4">
          {!file && (
            <div
              className={`relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all animate-fade-up ${
                drag
                  ? 'border-accent2 bg-accent2/10 scale-[1.01]'
                  : 'border-border hover:border-accent2/60 hover:bg-white/[0.02]'
              }`}
              onDragOver={e => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={e => {
                e.preventDefault()
                setDrag(false)
                const f = e.dataTransfer.files?.[0]
                if (f) handleFile(f)
              }}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept="video/*"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) handleFile(f)
                }}
              />
              <div className={`mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-accent2/25 to-accent/15 border border-white/10 flex items-center justify-center text-accent2 mb-4 transition-transform ${drag ? 'scale-110' : ''}`}>
                <IconUpload size={24} />
              </div>
              <p className="text-sm text-text-bright font-medium">
                拖拽视频到此处，或 <span className="text-accent2 underline underline-offset-4">点击上传</span>
              </p>
              <p className="text-[11px] text-text-dim mt-2">MP4 / MOV / AVI / WebM / MKV，最大 200MB</p>
            </div>
          )}

          {file && (
            <div className="rounded-2xl border border-border bg-surface/80 backdrop-blur p-3 flex items-center gap-3 animate-fade-up">
              <span className="w-11 h-11 rounded-xl bg-accent2/15 border border-white/10 flex items-center justify-center text-accent2 shrink-0">
                <IconVideo size={19} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-text-bright truncate">{file.name}</p>
                <p className="text-[10px] text-text-dim">{(file.size / 1024 / 1024).toFixed(1)} MB · {duration ? `${duration.toFixed(1)}s` : '读取中...'}</p>
              </div>
              {!busy && (
                <button onClick={reset} className="btn-ghost w-8 h-8 rounded-lg flex items-center justify-center text-text-dim" aria-label="移除视频">
                  <IconX size={14} />
                </button>
              )}
            </div>
          )}

          {file && !done && (
            <div className="rounded-2xl border border-border bg-surface/50 backdrop-blur p-4 space-y-5 animate-fade-up">
              {/* style */}
              <div>
                <div className="text-[11px] text-text-dim uppercase tracking-wider font-medium mb-2.5">风格滤镜</div>
                <StyleSelector styles={styleOpts} selected={style} onChange={setStyle} allowAll={false} compact />
              </div>

              {/* trim */}
              <div className="rounded-xl border border-border bg-surface p-3.5">
                <div className="flex items-center justify-between mb-2.5">
                  <span className="text-[11px] text-text-dim uppercase tracking-wider font-medium flex items-center gap-1.5">
                    <IconScissors size={12} /> 裁剪片段
                  </span>
                  <span className="text-[11px] text-text-bright font-mono">
                    {fmtTime(start)} — {fmtTime(end)}
                    {duration > 0 && <span className="text-text-dim"> / {fmtTime(duration)}</span>}
                  </span>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-[10px] text-text-dim mb-1"><span>起点</span><span>{fmtTime(start)}</span></div>
                    <input
                      type="range"
                      min={0}
                      max={Math.max(0, duration - 0.2)}
                      step={0.1}
                      value={Math.min(start, Math.max(0, duration - 0.2))}
                      disabled={duration === 0 || busy}
                      onChange={e => setStart(Math.min(parseFloat(e.target.value), end - 0.2))}
                      className="w-full accent-[#d946ef]"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] text-text-dim mb-1"><span>终点</span><span>{fmtTime(end)}</span></div>
                    <input
                      type="range"
                      min={0}
                      max={duration}
                      step={0.1}
                      value={end}
                      disabled={duration === 0 || busy}
                      onChange={e => setEnd(Math.max(parseFloat(e.target.value), start + 0.2))}
                      className="w-full accent-[#d946ef]"
                    />
                  </div>
                  <div className="h-1.5 rounded-full bg-surface3 relative overflow-hidden">
                    <div
                      className="absolute top-0 bottom-0 bg-gradient-to-r from-accent2 to-accent opacity-80"
                      style={{ left: `${duration ? (start / duration) * 100 : 0}%`, width: `${duration ? ((end - start) / duration) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* quality */}
              <div>
                <div className="text-[11px] text-text-dim uppercase tracking-wider font-medium mb-2">输出清晰度</div>
                <div className="grid grid-cols-4 gap-1.5">
                  {VIDEO_QUALITIES.map(q => (
                    <button
                      key={q}
                      onClick={() => setQuality(q)}
                      disabled={busy}
                      className={`py-1.5 rounded-lg text-xs font-medium border transition-all ${
                        quality === q
                          ? 'border-accent2 bg-accent2/15 text-accent2'
                          : 'border-border text-text-dim hover:text-text-bright hover:border-border-hover'
                      }`}
                    >
                      {QUALITY_LABELS[q]}
                    </button>
                  ))}
                </div>
              </div>

              {/* process */}
              <button
                onClick={startProcess}
                disabled={busy || duration === 0}
                className="btn-primary w-full py-3 rounded-xl text-sm font-semibold text-white inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {busy ? <><span className="animate-spin w-4 h-4 border-2 border-white/40 border-t-white rounded-full" /> 处理中...</> : (
                  <><IconPlay size={15} /> 开始风格化</>
                )}
              </button>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-xs text-danger animate-fade-in">
              {error}
            </div>
          )}

          <ProcessingStatus status={busy ? 'processing' : job?.status === 'error' ? 'error' : job?.status === 'done' ? 'done' : 'idle'} message={job?.message} progress={job?.progress} />
        </aside>

        {/* ============ right: preview ============ */}
        <section className="min-h-[300px]">
          {!file && (
            <div className="h-full min-h-[300px] rounded-3xl border border-dashed border-border flex flex-col items-center justify-center text-center p-10">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-accent2/15 to-accent/10 border border-white/5 flex items-center justify-center mb-4">
                <IconVideo size={26} className="text-accent2/70" />
              </div>
              <p className="text-sm text-text-bright font-medium">上传视频后，在这里预览与处理</p>
              <p className="text-[11px] text-text-dim mt-1.5">支持裁剪任意片段、选择风格与清晰度，实时查看进度</p>
            </div>
          )}

          {file && (
            <div className="space-y-4 animate-fade-up">
              {/* source player */}
              <div className="rounded-2xl border border-border bg-surface/80 backdrop-blur overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/60">
                  <span className="text-[11px] text-text-dim flex items-center gap-1.5">
                    <IconClock size={12} /> 原视频
                  </span>
                  <span className="text-[10px] text-text-dim">{duration ? fmtTime(duration) : ''}</span>
                </div>
                <video
                  ref={videoRef}
                  src={videoUrl}
                  controls
                  playsInline
                  onLoadedMetadata={onMetadata}
                  className="w-full max-h-[420px] bg-black"
                />
              </div>

              {/* result */}
              {done && job?.result && (
                <div className="rounded-2xl border border-success/30 bg-surface/80 backdrop-blur overflow-hidden animate-fade-up">
                  <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/60">
                    <span className="text-[11px] text-success flex items-center gap-1.5 font-medium">
                      <IconCheck size={12} /> 处理完成 · {job.result.style_name}
                    </span>
                    <a
                      href={resultUrl}
                      download={job.result.output_filename}
                      className="btn-ghost inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-text-bright"
                    >
                      <IconDownload size={13} /> 下载成品
                    </a>
                  </div>
                  <video src={resultUrl} controls playsInline className="w-full max-h-[420px] bg-black" />
                  <div className="px-4 py-2.5 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-text-dim border-t border-border/60">
                    <span>时长 {job.result.duration}s</span>
                    <span>{job.result.width}×{job.result.height}</span>
                    <span>{job.result.frames} 帧</span>
                    <span>{job.result.fps} fps</span>
                    <span>{job.result.has_audio ? '含原声' : '无音轨'}</span>
                  </div>
                </div>
              )}

              {/* re-edit */}
              {done && (
                <button
                  onClick={reset}
                  className="btn-ghost w-full py-3 rounded-xl text-sm text-text-bright inline-flex items-center justify-center gap-2"
                >
                  <IconRefresh size={15} /> 重新剪辑
                </button>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
