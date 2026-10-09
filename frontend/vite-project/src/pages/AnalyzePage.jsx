import { useCallback, useEffect, useRef, useState } from 'react'
import { analyzeVideo, ApiError, validateVideoFile } from '../api.js'
import ConnectionStatus from '../components/ConnectionStatus.jsx'
import UploadZone from '../components/UploadZone.jsx'
import ResultCard from '../components/ResultCard.jsx'
import { AlertIcon } from '../components/Icons.jsx'

export default function AnalyzePage() {
  const [file, setFile] = useState(null)
  const [validationError, setValidationError] = useState(null)
  const [status, setStatus] = useState('idle') // 'idle' | 'analyzing' | 'done' | 'error'
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [recheckKey, setRecheckKey] = useState(0)

  const inFlight = useRef(false) // guards against duplicate submissions
  const controllerRef = useRef(null)

  // Cancel any running request if the user leaves the page.
  useEffect(() => () => controllerRef.current?.abort(), [])

  const reset = () => {
    setResult(null)
    setError(null)
    setStatus('idle')
  }

  const handleSelect = useCallback((selected) => {
    if (inFlight.current) return
    reset()
    const problem = validateVideoFile(selected)
    setFile(selected)
    setValidationError(problem)
  }, [])

  const handleRemove = useCallback(() => {
    if (inFlight.current) return
    reset()
    setFile(null)
    setValidationError(null)
  }, [])

  const handleAnalyze = async () => {
    if (inFlight.current || !file || validationError) return
    inFlight.current = true
    const controller = new AbortController()
    controllerRef.current = controller
    setResult(null)
    setError(null)
    setStatus('analyzing')

    try {
      const parsed = await analyzeVideo(file, { signal: controller.signal })
      setResult(parsed)
      setStatus('done')
    } catch (err) {
      if (err instanceof ApiError && err.kind === 'aborted') {
        setStatus('idle')
      } else {
        const apiError =
          err instanceof ApiError
            ? err
            : new ApiError('format', 'Something went wrong while analyzing this video.')
        setError(apiError)
        setStatus('error')
        if (apiError.kind === 'network') setRecheckKey((k) => k + 1)
      }
    } finally {
      inFlight.current = false
      controllerRef.current = null
    }
  }

  const analyzing = status === 'analyzing'
  const canAnalyze = Boolean(file) && !validationError && !analyzing

  return (
    <div className="container page">
      <div className="page-head">
        <h1>Analyze a video</h1>
        <p className="lead">
          Upload a video to run it through the analysis pipeline. Results are shown exactly as the
          server returns them.
        </p>
        <ConnectionStatus recheckKey={recheckKey} />
      </div>

      <section className="card workspace" aria-label="Video upload">
        <UploadZone
          file={file}
          onSelect={handleSelect}
          onRemove={handleRemove}
          disabled={analyzing}
          error={validationError}
        />

        <div className="actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            aria-busy={analyzing}
          >
            {analyzing && <span className="spinner" aria-hidden="true" />}
            {analyzing ? 'Analyzing…' : 'Analyze Video'}
          </button>
          {analyzing && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => controllerRef.current?.abort()}
            >
              Cancel
            </button>
          )}
        </div>

        {analyzing && (
          <div className="progress" role="status" aria-live="polite">
            <div className="progress-bar" aria-hidden="true">
              <span />
            </div>
            <p className="muted">
              Uploading and analyzing. This can take a while for longer videos. Please keep this
              page open.
            </p>
          </div>
        )}
      </section>

      {status === 'error' && error && (
        <div className="notice notice-error" role="alert">
          <AlertIcon />
          <div>
            <p className="notice-title">The analysis could not be completed</p>
            <p>{error.message}</p>
            {error.retryable && file && !validationError && (
              <button type="button" className="btn btn-secondary" onClick={handleAnalyze}>
                Try again
              </button>
            )}
          </div>
        </div>
      )}

      {status === 'done' && result && <ResultCard key={result.heatmapUrl || 'r'} result={result} />}

      {status === 'idle' && !file && (
        <p className="empty muted">Choose a video above to get started.</p>
      )}
    </div>
  )
}
