import { NavLink, Outlet, Link } from 'react-router-dom'
import { IconSparkles, IconImage, IconVideo } from './icons'

const navItems = [
  { to: '/image', label: '图片美化', icon: IconImage },
  { to: '/video', label: '视频风格化', icon: IconVideo },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 glass">
        <div className="mx-auto max-w-6xl h-14 px-4 sm:px-6 flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 group shrink-0">
            <span className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent via-accent2 to-accent3 flex items-center justify-center text-white shadow-lg shadow-accent/40 group-hover:scale-105 transition-transform">
              <IconSparkles size={17} />
            </span>
            <span className="text-[15px] font-semibold tracking-tight text-text-bright">
              AI 影像工坊
            </span>
          </Link>

          <nav className="flex items-center gap-1 ml-2">
            {navItems.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-all ${
                    isActive
                      ? 'bg-accent/15 text-accent-hover ring-1 ring-accent/30'
                      : 'text-text-dim hover:text-text-bright hover:bg-white/5'
                  }`
                }
              >
                <item.icon size={15} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto hidden sm:flex items-center gap-1.5 text-[11px] text-text-dim">
            <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
            OpenCV 分析 · DeepSeek 调参
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-border/60 py-6">
        <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-text-dim">
          <span>AI 影像工坊 · 图片美化 & 视频风格化</span>
          <span>OpenCV + DeepSeek · 免费视觉分析，无需额外 API</span>
        </div>
      </footer>
    </div>
  )
}
