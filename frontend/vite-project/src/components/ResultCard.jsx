import { useState } from 'react'
import { AlertIcon, CheckIcon, InfoIcon } from './Icons.jsx'

const fmtSeconds = (s) => (s < 10 ? s.toFixed(2) : s.toFixed(1))

function Verdict({ result }) {
  const { verdict, confidencePercent, frames } = result

  if (verdict === 'REAL' || verdict === 'FAKE') {
    const fake = verdict === 'FAKE'
    return (
      <div className={`verdict ${fake ? 'verdict-fake' : 'verdict-real'}`}>
        <span className="verdict-icon">{fake ? <AlertIcon /> : <CheckIcon />}</span>
        <div>
          <p className="verdict-label">{fake ? 'Classified as fake' : 'Classified as real'}</p>
          {confidencePercent !== null && (
            <p className="verdict-sub">Confidence: {confidencePercent.toFixed(1)}%</p>
          )}
        </div>
      </div>
    )
  }

  if (verdict === 'MODEL_UNAVAILABLE') {
    return (
      <div className="verdict verdict-neutral">
        <span className="verdict-icon">
          <InfoIcon />
        </span>
        <div>
          <p className="verdict-label">No classification available</p>
          <p className="verdict-sub">
            The video was processed, but a trained classification model isn’t currently integrated
            or available, so this video has not been labelled real or fake.
            {frames.usable === 0 && ' No usable face frames were found in the sampled frames.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="verdict verdict-neutral">
      <span className="verdict-icon">
        <InfoIcon />
      </span>
      <div>
        <p className="verdict-label">Result not recognized</p>
        <p className="verdict-sub">The server returned a result this page can’t interpret.</p>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

export default function ResultCard({ result }) {
  const [imageFailed, setImageFailed] = useState(false)
  const { frames, video, processingSeconds, suspiciousStart, suspiciousEnd } = result

  const stats = []
  if (frames.sampled !== null) stats.push(['Frames sampled', frames.sampled])
  if (frames.facesDetected !== null) stats.push(['Frames with a face', frames.facesDetected])
  if (frames.withoutFace !== null) stats.push(['Frames without a face', frames.withoutFace])
  if (frames.blurred !== null) stats.push(['Blurry frames skipped', frames.blurred])
  if (frames.usable !== null) stats.push(['Usable face frames', frames.usable])
  if (video.durationSeconds !== null)
    stats.push(['Video length', `${fmtSeconds(video.durationSeconds)} s`])
  if (video.width !== null && video.height !== null && video.width > 0)
    stats.push(['Resolution', `${video.width} × ${video.height}`])
  if (processingSeconds !== null)
    stats.push(['Processing time', `${processingSeconds.toFixed(2)} s`])

  const showSegment =
    (result.verdict === 'REAL' || result.verdict === 'FAKE') &&
    suspiciousStart !== null &&
    suspiciousEnd !== null

  return (
    <section className="card result" aria-labelledby="result-title">
      <h2 id="result-title" className="card-title">
        Analysis result
      </h2>

      <Verdict result={result} />

      {showSegment && (
        <p className="result-line">
          Flagged segment: {fmtSeconds(suspiciousStart)} s – {fmtSeconds(suspiciousEnd)} s
        </p>
      )}

      {result.artifacts.length > 0 && (
        <div className="result-line">
          <span className="muted">Reported artifacts: </span>
          {result.artifacts.join(', ')}
        </div>
      )}

      {stats.length > 0 && (
        <dl className="stats">
          {stats.map(([label, value]) => (
            <Stat key={label} label={label} value={value} />
          ))}
        </dl>
      )}

      {result.heatmapUrl && !imageFailed && (
        <figure className="figure">
          <img
            src={result.heatmapUrl}
            alt="Development visualization of an analyzed face frame"
            onError={() => setImageFailed(true)}
          />
          <figcaption>
            <strong>Development visualization.</strong> This is a simple edge-based overlay on one
            analyzed face frame. It is not Grad-CAM and does not show what a model paid attention
            to.
            {result.note && <span className="muted"> Server note: {result.note}</span>}
          </figcaption>
        </figure>
      )}

      {result.model.demoMode === true && (
        <p className="muted small">The server is running in demo mode.</p>
      )}
    </section>
  )
}
