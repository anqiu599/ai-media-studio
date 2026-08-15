export interface StyleInfo {
  key: string;
  name: string;
  description: string;
  icon: string;
  preview?: [string, string];
}

export interface ImageResult {
  style_key: string;
  style_name: string;
  style_icon: string;
  description: string;
  ai_analysis: string;
  output_path: string;
  output_filename: string;
  error?: string;
}

export interface ProcessResponse<T> {
  total_styles: number;
  success_count: number;
  error_count: number;
  results: T[];
  errors: { style_key: string; error: string }[] | null;
}

// ---------------- Video ----------------

export interface VideoProcessResult {
  output_filename: string;
  style_key: string;
  style_name: string;
  duration: number;
  frames: number;
  fps: number;
  width: number;
  height: number;
  has_audio: boolean;
}

export type VideoJobStatus = 'queued' | 'processing' | 'done' | 'error'

export interface VideoJob {
  status: VideoJobStatus;
  progress: number;
  message: string;
  result: VideoProcessResult | null;
  error: string | null;
}

export interface VideoProcessResponse {
  job_id: string;
}

export const VIDEO_QUALITIES = ['original', '1080p', '720p', '480p'] as const
export type VideoQuality = (typeof VIDEO_QUALITIES)[number]

export const QUALITY_LABELS: Record<VideoQuality, string> = {
  original: '原画质',
  '1080p': '1080P',
  '720p': '720P',
  '480p': '480P',
}
