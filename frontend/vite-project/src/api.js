/**
 * API client for the FastAPI backend.
 *
 * Verified against backend/app:
 *   GET  /api/v1/health    -> { status, service }
 *   POST /api/v1/analysis  -> multipart/form-data, field name "file"
 *   Heatmap images are served from /outputs/<name>.jpg (outside /api/v1)
 *
 * In development, Vite proxies /api and /outputs to the backend (see
 * vite.config.js), so the default base URL is empty (same origin).
 * Set VITE_API_BASE_URL to call a backend on another origin directly
 * (the backend's CORS_ORIGINS must then allow this site's origin).
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')
const API_PREFIX = '/api/v1'

export const ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov']

// Matches the backend default (max_upload_size_mb = 500). The server value is
// not exposed by any endpoint, so this is only a client-side pre-check; the
// server remains the authority.
export const MAX_UPLOAD_MB = Number(import.meta.env.VITE_MAX_UPLOAD_MB) || 500

// Server-side analysis of a large video can take a while, so the timeout is generous.
const ANALYSIS_TIMEOUT_MS = 10 * 60 * 1000
const HEALTH_TIMEOUT_MS = 5000

export class ApiError extends Error {
  /**
   * @param {'network'|'timeout'|'aborted'|'http'|'format'} kind
   */
  constructor(kind, message, { status = null, retryable = true } = {}) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.retryable = retryable
  }
}

/** fetch() with a timeout and optional external abort signal. */
async function request(url, options = {}, { timeoutMs, signal } = {}) {
  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)
  const onExternalAbort = () => controller.abort()
  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', onExternalAbort, { once: true })
  }

  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } catch (err) {
    if (timedOut) {
      throw new ApiError(
        'timeout',
        'The analysis is taking longer than expected and was stopped. Try a shorter video or try again.'
      )
    }
    if (err?.name === 'AbortError') {
      throw new ApiError('aborted', 'The request was cancelled.', { retryable: true })
    }
    throw new ApiError('network', UNREACHABLE_MESSAGE)
  } finally {
    clearTimeout(timer)
    if (signal) signal.removeEventListener('abort', onExternalAbort)
  }
}

/** Reads the response body as JSON, or returns null if it is not JSON. */
async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

const UNREACHABLE_MESSAGE =
  'Could not reach the analysis server. Make sure the backend is running, then try again.'

/** Turns a non-2xx response into a user-friendly ApiError (never exposes internals). */
async function toHttpError(response) {
  const status = response.status
  let text = ''
  try {
    text = await response.text()
  } catch {
    text = ''
  }
  let body = null
  try {
    body = JSON.parse(text)
  } catch {
    body = null
  }
  const detail = body && typeof body.detail === 'string' ? body.detail : null

  // A gateway/proxy answers 502/503/504 when the backend is down. The Vite dev
  // proxy answers 500 with an empty body when it cannot connect. A real FastAPI
  // error always has a body, so an empty 500 means "backend unreachable".
  if (status === 502 || status === 503 || status === 504 || (status === 500 && !text.trim())) {
    return new ApiError('network', UNREACHABLE_MESSAGE, { status })
  }

  if (status === 400) {
    // The backend's 400 messages are short validation messages meant for users
    // (unsupported format, size limit, unreadable video).
    return new ApiError('http', detail || 'The server could not accept this video.', {
      status,
      retryable: false,
    })
  }
  if (status === 413) {
    return new ApiError('http', 'This video is too large for the server to accept.', {
      status,
      retryable: false,
    })
  }
  if (status === 422) {
    return new ApiError(
      'http',
      'The server could not read the upload. Please choose the video file again.',
      { status, retryable: false }
    )
  }
  if (status >= 500) {
    return new ApiError(
      'http',
      'The server ran into a problem while analyzing this video. Please try again, or try a different video.',
      { status }
    )
  }
  return new ApiError('http', `The server returned an unexpected response (HTTP ${status}).`, {
    status,
  })
}

/** GET /api/v1/health. Resolves true only if the backend reports status "ok". */
export async function checkHealth(signal) {
  try {
    const response = await request(
      `${API_BASE}${API_PREFIX}/health`,
      { method: 'GET' },
      { timeoutMs: HEALTH_TIMEOUT_MS, signal }
    )
    if (!response.ok) return false
    const body = await readJson(response)
    return Boolean(body && body.status === 'ok')
  } catch {
    return false
  }
}

const isNum = (v) => typeof v === 'number' && Number.isFinite(v)
const numOrNull = (v) => (isNum(v) ? v : null)

/**
 * Only same-origin style paths under /outputs/ are accepted, so a malformed or
 * hostile response cannot make the page load an arbitrary URL.
 */
export function resolveOutputUrl(path) {
  if (typeof path !== 'string') return null
  if (!/^\/outputs\/[\w.\-]+$/.test(path)) return null
  return `${API_BASE}${path}`
}

/**
 * Validates and normalises the /analysis response. Throws ApiError('format')
 * if the essential structure is missing. Every other field is optional and is
 * returned as null when absent, so the UI shows only what the API provided.
 */
export function parseAnalysisResponse(data) {
  const detection = data && typeof data === 'object' ? data.detection : null
  if (!detection || typeof detection !== 'object' || typeof detection.verdict !== 'string') {
    throw new ApiError(
      'format',
      'The server returned a response this page does not understand. Please try again.'
    )
  }

  const pre = data.preprocessing && typeof data.preprocessing === 'object' ? data.preprocessing : {}
  const video = data.video && typeof data.video === 'object' ? data.video : {}
  const model = data.model && typeof data.model === 'object' ? data.model : {}
  const meta = data.meta && typeof data.meta === 'object' ? data.meta : {}
  const timeline =
    detection.timeline && typeof detection.timeline === 'object' ? detection.timeline : {}

  const confidencePercent = isNum(detection.confidence_percent)
    ? detection.confidence_percent
    : isNum(detection.confidence)
      ? detection.confidence * 100
      : null

  return {
    verdict: detection.verdict.toUpperCase(),
    confidencePercent,
    artifacts: Array.isArray(detection.artifacts)
      ? detection.artifacts.filter((a) => typeof a === 'string' && a.trim())
      : [],
    suspiciousStart: numOrNull(timeline.suspicious_start),
    suspiciousEnd: numOrNull(timeline.suspicious_end),
    frames: {
      sampled: numOrNull(pre.frames_sampled),
      facesDetected: numOrNull(pre.faces_detected),
      withoutFace: numOrNull(pre.frames_without_face),
      blurred: numOrNull(pre.blurred_frames),
      usable: numOrNull(pre.usable_frames),
    },
    video: {
      filename: typeof video.filename === 'string' ? video.filename : null,
      durationSeconds: numOrNull(video.duration_seconds),
      width: numOrNull(video.width),
      height: numOrNull(video.height),
    },
    model: {
      name: typeof model.name === 'string' ? model.name : null,
      demoMode: typeof model.demo_mode === 'boolean' ? model.demo_mode : null,
    },
    processingSeconds: numOrNull(meta.processing_time_seconds),
    heatmapUrl: resolveOutputUrl(meta.heatmap_url),
    note: typeof meta.note === 'string' && meta.note.trim() ? meta.note : null,
  }
}

/**
 * POST /api/v1/analysis with the selected video.
 * FormData sets the multipart Content-Type (with boundary) itself, so no
 * Content-Type header is set manually.
 *
 * Note: fetch() exposes no upload progress, so the UI uses an indeterminate
 * indicator rather than a fabricated percentage.
 */
export async function analyzeVideo(file, { signal } = {}) {
  const form = new FormData()
  form.append('file', file, file.name)

  const response = await request(
    `${API_BASE}${API_PREFIX}/analysis`,
    { method: 'POST', body: form },
    { timeoutMs: ANALYSIS_TIMEOUT_MS, signal }
  )

  if (!response.ok) throw await toHttpError(response)

  const data = await readJson(response)
  return parseAnalysisResponse(data)
}

/** Client-side pre-check. Returns an error message, or null if the file looks acceptable. */
export function validateVideoFile(file) {
  if (!file) return 'Please choose a video file.'
  const name = file.name || ''
  const dot = name.lastIndexOf('.')
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : ''
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type${ext ? ` (${ext})` : ''}. Please choose an MP4, AVI or MOV video.`
  }
  if (file.size === 0) return 'This file is empty. Please choose a different video.'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `This video is ${formatBytes(file.size)}, which is over the ${MAX_UPLOAD_MB} MB limit.`
  }
  return null
}

export function formatBytes(bytes) {
  if (!isNum(bytes)) return ''
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let i = 0
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024
    i += 1
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${units[i]}`
}
