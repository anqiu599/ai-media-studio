import { useCallback, useRef, useState } from 'react'

interface Props {
  before: string
  after: string
  beforeLabel?: string
  afterLabel?: string
  className?: string
}

/**
 * Draggable before/after comparison slider.
 * Drag the handle (or click anywhere) to reveal the processed result.
 */
export default function CompareSlider({ before, after, beforeLabel = '原图', afterLabel = '处理后', className = '' }: Props) {
  const [pos, setPos] = useState(50)
  const [dragging, setDragging] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const update = useCallback((clientX: number) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const pct = ((clientX - rect.left) / rect.width) * 100
    setPos(Math.min(100, Math.max(0, pct)))
  }, [])

  return (
    <div
      ref={ref}
      className={`relative select-none overflow-hidden touch-none cursor-ew-resize ${className}`}
      onPointerDown={e => {
        setDragging(true)
        ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
        update(e.clientX)
      }}
      onPointerMove={e => {
        if (dragging) update(e.clientX)
      }}
      onPointerUp={() => setDragging(false)}
      onPointerCancel={() => setDragging(false)}
    >
      {/* after (base layer) */}
      <img src={after} alt={afterLabel} className="absolute inset-0 w-full h-full object-cover" draggable={false} />
      {/* before (clipped) */}
      <img
        src={before}
        alt={beforeLabel}
        className="absolute inset-0 w-full h-full object-cover"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
        draggable={false}
      />

      {/* labels */}
      <span className="absolute top-2 left-2 text-[10px] px-2 py-0.5 rounded-full bg-black/60 backdrop-blur text-white/90 pointer-events-none">
        {beforeLabel}
      </span>
      <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-accent/80 backdrop-blur text-white pointer-events-none">
        {afterLabel}
      </span>

      {/* divider + handle */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-white/90 shadow-[0_0_12px_rgba(0,0,0,0.5)] pointer-events-none"
        style={{ left: `${pos}%`, transform: 'translateX(-50%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white shadow-lg flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6d5efc" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 6l-5 6 5 6M16 6l5 6-5 6" />
          </svg>
        </div>
      </div>
    </div>
  )
}
