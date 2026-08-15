import { useRef, useState } from 'react'

interface Props {
  accept: string
  maxSizeMB?: number
  onUpload: (file: File) => void
  disabled?: boolean
  hint?: string
}

export default function FileUploader({ accept, maxSizeMB = 500, onUpload, disabled, hint }: Props) {
  const [drag, setDrag] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handle = (file: File) => {
    setError('')
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`文件不能超过 ${maxSizeMB}MB`)
      return
    }
    onUpload(file)
  }

  return (
    <div
      className={`relative rounded-xl border-2 border-dashed p-16 text-center transition-colors cursor-pointer ${
        drag ? 'border-accent bg-accent/5' : 'border-border hover:border-border-hover'
      } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      onDragOver={e => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={e => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) handle(f) }}
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} type="file" accept={accept} className="hidden"
        onChange={e => { const f = e.target.files?.[0]; if (f) handle(f) }} />
      <div className="text-3xl mb-3 opacity-30">+</div>
      <p className="text-sm text-text-dim">
        拖拽文件到此处，或<span className="text-accent">点击上传</span>
      </p>
      <p className="text-[11px] text-text-dim mt-2">{hint}</p>
      {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
    </div>
  )
}
