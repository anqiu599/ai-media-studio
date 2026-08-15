import { useCallback, useEffect, useRef, useState } from 'react'
import StyleSelector from '../components/StyleSelector'
import ProcessingStatus from '../components/ProcessingStatus'
import ImageResultCard from '../components/ImageResultCard'
import { getImageStyles, processImage } from '../services/api'
import type { StyleInfo, ImageResult } from '../types'
import { IconImage, IconRefresh, IconUpload, IconWand, IconX } from '../components/icons'

type Status = 'idle' | 'processing' | 'done' | 'error'

const MAX_SIZE = 50 * 1024 * 1024

export default function ImagePage() {
  const [styles, setStyles] = useState<Record<string, StyleInfo>>({})
  const [style, setStyle] = useState('all')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [msg, setMsg] = useState('')
  const [results, setResults] = useState<ImageResult[]>([])
  const [errors, setErrors] = useState<{ style_key: string; error: string }[]>([])
  const [drag, setDrag] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { getImageStyles().then(setStyles).catch(console.error) }, [])

  const submit = useCallback(async (f: File, sty: string) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setStatus('processing')
    setMsg('AI 分析画面并调参中...')
    setResults([])
    setErrors([])
    try {
      const res = await processImage(f, sty)
      setResults(res.results)
      setErrors(res.errors || [])
      setStatus('done')
      setMsg(`完成 ${res.success_count}/${res.total_styles} 种风格`)
    } catch (e) {
      setStatus('error')
      setMsg(e instanceof Error ? e.message : '处理失败')
    }
  }, [])

  const handleFile = useCallback((f: File) => {
    if (f.size > MAX_SIZE) {
      setMsg('文件不能超过 50MB')
      setStatus('error')
      return
    }
    submit(f, style)
  }, [style, submit])

  const reset = () => {
    setFile(null)
    setResults([])
    setStatus('idle')
    setMsg('')
    setErrors([])
    if (preview) URL.revokeObjectURL(preview)
    setPreview('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const styleOpts = Object.fromEntries(
    Object.entries(styles).map(([k, v]) => [k, { ...v, key: k }])
  )

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
      {/* page header */}
      <div className="mb-6 animate-fade-up">
        <div className="inline-flex items-center gap-1.5 text-[11px] text-accent-hover font-medium mb-1.5">
          <IconImage size={13} /> 图片美化
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-text-bright tracking-tight">AI 图片美化</h1>
        <p className="text-xs text-text-dim mt-1">
          上传照片，AI 分析光影色彩后批量生成 {Object.keys(styles).length || 9} 种风格 · 拖动滑块对比效果
        </p>
      </div>

      <div className="grid lg:grid-cols-[400px_1fr] gap-6 items-start">
        {/* ============ left: upload + controls ============ */}
        <aside className="lg:sticky lg:top-20 space-y-4">
          {/* Upload dropzone */}
          {!file && (
            <div
              className={`relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all animate-fade-up ${
                drag
                  ? 'border-accent bg-accent/10 scale-[1.01]'
                  : 'border-border hover:border-accent/60 hover:bg-white/[0.02]'
              } ${status === 'processing' ? 'pointer-events-none opacity-50' : ''}`}
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
                id="file-input"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) handleFile(f)
                }}
              />
              <div className={`mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-accent/25 to-accent3/15 border border-white/10 flex items-center justify-center text-accent-hover mb-4 transition-transform ${drag ? 'scale-110' : ''}`}>
                <IconUpload size={24} />
              </div>
              <p className="text-sm text-text-bright font-medium">
                拖拽图片到此处，或 <span className="text-accent-hover underline underline-offset-4">点击上传</span>
              </p>
              <p className="text-[11px] text-text-dim mt-2">JPEG / PNG / WebP / BMP，最大 50MB</p>
            </div>
          )}

          {/* File info */}
          {file && (
            <div className="rounded-2xl border border-border bg-surface/80 backdrop-blur p-3 flex items-center gap-3 animate-fade-up">
              <img src={preview} alt="" className="w-14 h-14 rounded-xl object-cover border border-border" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-text-bright truncate">{file.name}</p>
                <p className="text-[10px] text-text-dim">{(file.size / 1024).toFixed(0)} KB</p>
              </div>
              {status !== 'processing' && (
                <button
                  onClick={reset}
                  className="btn-ghost w-8 h-8 rounded-lg flex items-center justify-center text-text-dim"
                  aria-label="移除文件"
                >
                  <IconX size={14} />
                </button>
              )}
            </div>
          )}

          {/* Style picker */}
          {!results.length && status !== 'processing' && Object.keys(styles).length > 0 && (
            <div className="rounded-2xl border border-border bg-surface/50 backdrop-blur p-4 animate-fade-up space-y-4">
              <StyleSelector styles={styleOpts} selected={style} onChange={setStyle} />
              {file && (
                <button
                  onClick={() => submit(file, style)}
                  className="btn-primary w-full py-3 rounded-xl text-sm font-semibold text-white inline-flex items-center justify-center gap-2"
                >
                  <IconWand size={16} />
                  {style === 'all' ? `生成全部 ${Object.keys(styles).length} 种风格` : '开始处理'}
                </button>
              )}
            </div>
          )}

          {/* Status */}
          <ProcessingStatus status={status} message={msg} />
        </aside>

        {/* ============ right: results ============ */}
        <section className="min-h-[300px]">
          {results.length === 0 && status === 'idle' && (
            <div className="h-full min-h-[300px] rounded-3xl border border-dashed border-border flex flex-col items-center justify-center text-center p-10">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-accent/15 to-accent2/10 border border-white/5 flex items-center justify-center mb-4">
                <IconWand size={26} className="text-accent-hover/70" />
              </div>
              <p className="text-sm text-text-bright font-medium">上传照片后，结果将展示在这里</p>
              <p className="text-[11px] text-text-dim mt-1.5">每张风格图都支持左右拖动，直观对比前后效果</p>
            </div>
          )}

          {results.length > 0 && (
            <div className="animate-fade-up space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-text-bright flex items-center gap-2">
                  <IconImage size={15} className="text-accent-hover" />
                  处理结果
                  <span className="text-[11px] font-normal text-text-dim">{results.length} 种风格</span>
                </h2>
                <button
                  onClick={reset}
                  className="btn-ghost inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-text-bright"
                >
                  <IconRefresh size={13} />
                  重新上传
                </button>
              </div>

              {errors.length > 0 && (
                <div className="rounded-xl border border-warn/25 bg-warn/10 p-3 space-y-1">
                  {errors.map((e, i) => (
                    <p key={i} className="text-[11px] text-warn">{e.style_key}: {e.error}</p>
                  ))}
                </div>
              )}

              <div className="grid sm:grid-cols-2 gap-4">
                {results.map(r => (
                  <ImageResultCard key={r.style_key} result={r} originalUrl={preview} />
                ))}
              </div>
            </div>
          )}

          {status === 'processing' && (
            <div className="h-full min-h-[300px] rounded-3xl border border-border bg-surface/40 flex items-center justify-center">
              <div className="text-center">
                <div className="mx-auto w-12 h-12 rounded-2xl bg-gradient-to-br from-accent to-accent2 flex items-center justify-center animate-float mb-4">
                  <IconWand size={22} className="text-white" />
                </div>
                <p className="text-xs text-text-dim">正在为你打造专属风格...</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
