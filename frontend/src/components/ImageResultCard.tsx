import type { ImageResult } from '../types'
import { getImageDownloadUrl } from '../services/api'
import CompareSlider from './CompareSlider'
import { IconDownload } from './icons'

interface Props {
  result: ImageResult
  originalUrl: string
}

export default function ImageResultCard({ result, originalUrl }: Props) {
  if (result.error) {
    return (
      <div className="rounded-xl border border-danger/25 bg-danger/10 p-4">
        <p className="text-xs text-danger">{result.style_name}: {result.error}</p>
      </div>
    )
  }

  const downloadUrl = getImageDownloadUrl(result.output_filename)

  return (
    <div className="card-hover group rounded-2xl border border-border bg-surface/80 backdrop-blur overflow-hidden flex flex-col animate-fade-up">
      <div className="relative">
        <CompareSlider
          before={originalUrl}
          after={downloadUrl}
          beforeLabel="原图"
          afterLabel={`${result.style_icon} ${result.style_name}`}
          className="w-full aspect-[4/3]"
        />
      </div>

      <div className="p-3.5 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[13px] font-semibold text-text-bright flex items-center gap-1.5">
            <span className="text-sm leading-none">{result.style_icon}</span>
            {result.style_name}
          </div>
          {result.ai_analysis && (
            <div className="text-[11px] text-text-dim mt-1 leading-snug line-clamp-2">{result.ai_analysis}</div>
          )}
        </div>
        <a
          href={downloadUrl}
          download={result.output_filename}
          className="btn-ghost shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-text-bright"
        >
          <IconDownload size={13} />
          下载
        </a>
      </div>
    </div>
  )
}
