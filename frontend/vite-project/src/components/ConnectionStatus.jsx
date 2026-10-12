import { useCallback, useEffect, useState } from 'react'
import { checkHealth } from '../api.js'

/**
 * Small indicator driven by the real GET /api/v1/health endpoint.
 * `recheckKey` lets the parent trigger a fresh check (e.g. after a network error).
 */
export default function ConnectionStatus({ recheckKey = 0 }) {
  const [state, setState] = useState('checking') // 'checking' | 'online' | 'offline'

  const run = useCallback((signal) => {
    setState('checking')
    checkHealth(signal).then((ok) => {
      if (!signal?.aborted) setState(ok ? 'online' : 'offline')
    })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    run(controller.signal)
    return () => controller.abort()
  }, [run, recheckKey])

  const label = {
    checking: 'Checking server…',
    online: 'Server connected',
    offline: 'Server not reachable',
  }[state]

  return (
    <div className="conn" role="status" aria-live="polite">
      <span className={`conn-dot conn-${state}`} aria-hidden="true" />
      <span>{label}</span>
      {state === 'offline' && (
        <button type="button" className="link-btn" onClick={() => run(undefined)}>
          Retry
        </button>
      )}
    </div>
  )
}
