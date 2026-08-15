import { IconCheck, IconLoader, IconX } from './icons'

interface Props {
  status: 'idle' | 'processing' | 'done' | 'error'
  message?: string
  progress?: number // 0-100, when provided shows determinate bar
}

export default function ProcessingStatus({ status, message, progress }: Props) {
  if (status === 'idle') return null

  if (status === 'processing') {
    return (
      <div className="rounded-2xl border border-border bg-surface/80 backdrop-blur px-5 py-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <span className="relative flex w-5 h-5 items-center justify-center">
            <span className="absolute inset-0 rounded-full bg-accent/30 animate-ping" />
            <IconLoader size={19} className="text-accent-hover relative" />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] text-text-bright font-medium truncate">{message ?? '处理中...'}</p>
            <div className="mt-2 h-1.5 rounded-full bg-surface3 overflow-hidden">
              {typeof progress === 'number' && progress > 0 ? (
                <div
                  className="h-full rounded-full bg-gradient-to-r from-accent via-accent2 to-accent3 transition-all duration-500"
                  style={{ width: `${Math.min(100, progress)}%` }}
                />
              ) : (
                <div className="h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-accent to-transparent animate-shimmer bg-[length:200%_100%]" />
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger/10 px-5 py-3.5 flex items-center gap-3 animate-fade-in">
        <IconX size={17} className="text-danger shrink-0" />
        <p className="text-[13px] text-danger">{message ?? '处理失败'}</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-success/25 bg-success/10 px-5 py-3.5 flex items-center gap-3 animate-fade-in">
      <span className="w-5 h-5 rounded-full bg-success/20 flex items-center justify-center shrink-0">
        <IconCheck size={13} className="text-success" />
      </span>
      <p className="text-[13px] text-success font-medium">{message ?? '处理完成'}</p>
    </div>
  )
}
