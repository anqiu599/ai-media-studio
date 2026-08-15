import type { StyleInfo } from '../types'

interface Props {
  styles: Record<string, StyleInfo>
  selected: string
  onChange: (key: string) => void
  allowAll?: boolean
  compact?: boolean
}

export default function StyleSelector({ styles, selected, onChange, allowAll = true, compact = false }: Props) {
  const list = Object.values(styles)

  return (
    <div>
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-[11px] text-text-dim uppercase tracking-wider font-medium">
          选择风格
        </span>
        {selected !== 'all' && (
          <button
            onClick={() => onChange('all')}
            className="text-[11px] text-accent-hover hover:underline"
          >
            全部生成
          </button>
        )}
      </div>

      <div className={`grid gap-2 ${compact ? 'grid-cols-3 sm:grid-cols-4 lg:grid-cols-5' : 'grid-cols-2 sm:grid-cols-3'}`}>
        {allowAll && (
          <button
            onClick={() => onChange('all')}
            className={`card-hover group relative rounded-xl border overflow-hidden text-left p-3 ${
              selected === 'all'
                ? 'border-accent bg-accent/10 ring-1 ring-accent/40'
                : 'border-border bg-surface hover:border-border-hover'
            }`}
          >
            <div className="h-8 rounded-lg mb-2 bg-gradient-to-r from-accent via-accent2 to-accent3 opacity-80 group-hover:opacity-100 transition-opacity" />
            <div className="text-[13px] font-medium text-text-bright">全部风格</div>
            <div className="text-[11px] text-text-dim mt-0.5 truncate">一次生成 {list.length} 种</div>
          </button>
        )}

        {list.map(s => {
          const [from, to] = s.preview ?? ['#6366f1', '#a855f7']
          const active = selected === s.key
          return (
            <button
              key={s.key}
              onClick={() => onChange(s.key)}
              className={`card-hover group relative rounded-xl border overflow-hidden text-left p-3 ${
                active
                  ? 'border-accent bg-accent/10 ring-1 ring-accent/40'
                  : 'border-border bg-surface hover:border-border-hover'
              }`}
            >
              <div
                className="h-8 rounded-lg mb-2 opacity-80 group-hover:opacity-100 transition-opacity"
                style={{ background: `linear-gradient(120deg, ${from}, ${to})` }}
              />
              <div className="text-[13px] font-medium text-text-bright flex items-center gap-1.5">
                <span className="text-sm leading-none">{s.icon}</span>
                {s.name}
              </div>
              <div className="text-[11px] text-text-dim mt-0.5 leading-snug line-clamp-2">{s.description}</div>
              {active && (
                <span className="absolute top-2 right-2 w-4 h-4 rounded-full bg-accent text-white flex items-center justify-center text-[10px]">
                  ✓
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
