import { HashRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ImagePage from './pages/ImagePage'
import VideoPage from './pages/VideoPage'

// HashRouter: 兼容 GitHub Pages 等纯静态托管（子路径下刷新/深链不 404）
function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/image" element={<ImagePage />} />
          <Route path="/video" element={<VideoPage />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}

export default App
