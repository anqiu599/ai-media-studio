import type {
  ImageResult,
  ProcessResponse,
  StyleInfo,
  VideoJob,
  VideoProcessResponse,
  VideoQuality,
} from '../types'

const BASE = '/api'

async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ---------------- Image ----------------

export async function getImageStyles(): Promise<Record<string, StyleInfo>> {
  return req('/image/styles')
}

export async function processImage(
  file: File,
  style: string = 'all'
): Promise<ProcessResponse<ImageResult>> {
  const form = new FormData()
  form.append('file', file)
  form.append('style', style)
  return req('/image/process', { method: 'POST', body: form })
}

export function getImageDownloadUrl(filename: string): string {
  return `${BASE}/image/download/${filename}`
}

// ---------------- Video ----------------

export async function getVideoStyles(): Promise<Record<string, StyleInfo>> {
  return req('/video/styles')
}

export async function processVideo(
  file: File,
  style: string,
  startSec: number,
  endSec: number,
  quality: VideoQuality
): Promise<VideoProcessResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('style', style)
  form.append('start_sec', String(startSec))
  form.append('end_sec', String(endSec))
  form.append('quality', quality)
  return req('/video/process', { method: 'POST', body: form })
}

export async function getVideoJobStatus(jobId: string): Promise<VideoJob> {
  return req(`/video/status/${jobId}`)
}

export function getVideoDownloadUrl(filename: string): string {
  return `${BASE}/video/download/${filename}`
}
