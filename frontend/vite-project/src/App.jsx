import { useState, useRef, useEffect, useCallback } from 'react'
import './App.css'

/* ══════════════════════════════════════════
   ICONS
══════════════════════════════════════════ */
function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg" style={{ width: 18, height: 18 }}>
      <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z" />
      <path
        d="M9 12l2 2 4-4"
        fill="none"
        stroke="white"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
    </svg>
  )
}

function VideoIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
  )
}

function ExternalLinkIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  )
}

/* ══════════════════════════════════════════
   NAVBAR
══════════════════════════════════════════ */
function Navbar({ activeSection, scrollTo }) {
  const links = ['Home', 'Upload', 'Dashboard', 'Features']

  return (
    <nav>
      <div className="nav-inner">
        <a
          className="nav-logo"
          href="#home"
          onClick={(e) => { e.preventDefault(); scrollTo('home') }}
        >
          <div className="logo-icon">
            <ShieldIcon />
          </div>
          DeepGuard AI
        </a>

        <div className="nav-links">
          {links.map((label) => (
            <a
              key={label}
              className={activeSection === label.toLowerCase() ? 'active' : ''}
              onClick={() => scrollTo(label.toLowerCase())}
            >
              {label}
            </a>
          ))}
        </div>

        <button className="btn-primary" onClick={() => scrollTo('upload')}>
          Start Detection
        </button>
      </div>
    </nav>
  )
}

/* ══════════════════════════════════════════
   HERO
══════════════════════════════════════════ */
function Hero({ scrollTo }) {
  return (
    <section id="home">
      {/* Background decorative circles */}
      <div
        className="hero-bg-circle"
        style={{
          width: 600,
          height: 600,
          background: 'radial-gradient(circle, rgba(99,102,241,.12) 0%, transparent 70%)',
          top: '10%',
          left: '5%',
        }}
      />
      <div
        className="hero-bg-circle"
        style={{
          width: 400,
          height: 400,
          background: 'radial-gradient(circle, rgba(168,85,247,.10) 0%, transparent 70%)',
          bottom: '15%',
          right: '8%',
        }}
      />

      <div className="hero-content fade-up">
        <div className="hero-badge">
          <span className="badge-dot" />
          Spatiotemporal Neural Networks Active
        </div>

        <h1 className="hero-title fade-up fade-up-delay-1">
          DeepFake Video<br />
          <span>Detection System</span>
        </h1>

        <p className="hero-sub fade-up fade-up-delay-2">
          AI-powered spatiotemporal analysis for detecting manipulated videos.
          Secure your media integrity with military-grade forensic analysis.
        </p>

        <div className="hero-btns fade-up fade-up-delay-3">
          <button className="btn-hero-primary" onClick={() => scrollTo('upload')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 16 12 12 8 16" />
              <line x1="12" y1="12" x2="12" y2="21" />
              <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
            </svg>
            Upload Video
          </button>
          <button className="btn-hero-outline" onClick={() => scrollTo('features')}>
            Learn More →
          </button>
        </div>
      </div>
    </section>
  )
}

/* ══════════════════════════════════════════
   UPLOAD & DETECTION SECTION
══════════════════════════════════════════ */
// status: 'idle' | 'uploading' | 'analyzing' | 'done'
function UploadSection() {
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState('idle')
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const fileRef = useRef()

  const handleFile = useCallback((f) => {
    if (!f) return
    setFile(f)
    setStatus('uploading')
    setProgress(0)
    setResult(null)

    let p = 0
    const iv = setInterval(() => {
      p += Math.random() * 18 + 6
      if (p >= 100) {
        clearInterval(iv)
        setProgress(100)
        setStatus('idle')
      } else {
        setProgress(Math.round(p))
      }
    }, 120)
  }, [])

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f) handleFile(f)
    },
    [handleFile]
  )

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const runAnalysis = () => {
    setStatus('analyzing')
    setTimeout(() => {
      setStatus('done')
      setResult({
        verdict: 'DEEPFAKE DETECTED',
        fake: true,
        confidence: 98.4,
        artifacts: 'Facial Blending, Eye Blink Anomalies',
        timeline: { suspicious: [7.5, 12.5], duration: 15 },
      })
    }, 2800)
  }

  const canAnalyze = file && status === 'idle'

  return (
    <section id="upload">
      <div className="section-inner">
        <div className="section-header">
          <h2>Secure Video Analysis</h2>
          <p>
            Upload suspicious media for deep neural network screening.
            We support standard formats up to 500 MB.
          </p>
        </div>

        <div className="upload-grid">
          {/* ── Left: Drop zone ── */}
          <div>
            <div
              className={`upload-box${dragOver ? ' drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <div className="upload-box-icon">
                {file ? <VideoIcon /> : <UploadIcon />}
              </div>

              <h3>{file ? file.name : 'Drag & Drop Video Here'}</h3>
              <p>Supported formats: MP4, AVI, MOV</p>

              <button
                className="btn-browse"
                onClick={(e) => { e.stopPropagation(); fileRef.current.click() }}
              >
                Browse Files
              </button>

              <input
                ref={fileRef}
                type="file"
                accept=".mp4,.avi,.mov,video/*"
                onChange={(e) => handleFile(e.target.files[0])}
              />

              {status === 'uploading' && (
                <div className="upload-progress" style={{ marginTop: 20 }}>
                  <div className="upload-progress-bar" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>

            {canAnalyze && (
              <button className="btn-analyze" onClick={runAnalysis}>
                🔍 Analyze Video
              </button>
            )}

            {status === 'analyzing' && (
              <button className="btn-analyze" disabled>
                Analyzing...
              </button>
            )}
          </div>

          {/* ── Right: Results card ── */}
          <div className="result-card">
            {/* Idle, no result */}
            {status !== 'analyzing' && !result && (
              <div
                style={{
                  padding: '56px 32px',
                  textAlign: 'center',
                  color: 'var(--gray-400)',
                }}
              >
                <div style={{ fontSize: 48, marginBottom: 16 }}>🎬</div>
                <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--gray-600)', marginBottom: 8 }}>
                  Analysis Results
                </p>
                <p style={{ fontSize: 14 }}>
                  Upload a video and click "Analyze Video" to get detection results.
                </p>
              </div>
            )}

            {/* Analyzing */}
            {status === 'analyzing' && (
              <div className="loading-wrap">
                <div className="spinner" />
                <div className="loading-bars">
                  <span /><span /><span /><span />
                </div>
                <p style={{ fontWeight: 600, color: 'var(--gray-700)' }}>
                  Running spatiotemporal analysis...
                </p>
                <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>
                  Checking CNN spatial features, facial landmarks, temporal motion patterns
                </p>
              </div>
            )}

            {/* Done */}
            {status === 'done' && result && (
              <>
                <div className="result-header">
                  <h3>Analysis Results</h3>
                  <div className={result.fake ? 'badge-fake' : 'badge-real'}>
                    <span>{result.fake ? '⚠' : '✓'}</span>
                    {result.verdict}
                  </div>
                </div>

                <div className="video-preview">
                  <div
                    style={{
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(135deg,#2d1b69,#1a1a3e)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      minHeight: 200,
                    }}
                  >
                    <div style={{ color: 'rgba(255,255,255,.3)', fontSize: 48 }}>🎥</div>
                  </div>
                  <div className="heatmap-overlay" />
                  <div className="video-overlay">
                    <div className="play-btn">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                        <polygon points="5 3 19 12 5 21 5 3" />
                      </svg>
                    </div>
                  </div>
                  <div className="video-timer">00:04 / 00:15</div>
                </div>

                <div className="result-stats">
                  <div className="stat-item">
                    <label>Confidence Score</label>
                    <div className={`stat-val ${result.fake ? 'danger' : 'safe'}`}>
                      {result.confidence}%
                    </div>
                  </div>
                  <div className="stat-item">
                    <label>Primary Artifacts</label>
                    <div className="stat-artifacts">{result.artifacts}</div>
                  </div>
                </div>

                <div className="timeline-section">
                  <label>Suspicious Frames Timeline</label>
                  <div className="timeline-bar">
                    <div className="tl-green" />
                    <div className="tl-red" />
                    <div className="tl-cursor" />
                    <div className="tl-red2" />
                    <div className="tl-green2" />
                  </div>
                  <div className="tl-times">
                    <span>0s</span>
                    <span>7.5s</span>
                    <span>15s</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ══════════════════════════════════════════
   DASHBOARD CHARTS
══════════════════════════════════════════ */
function BarChart() {
  const canvasRef = useRef()

  useEffect(() => {
    let chart = null

    // Dynamically import Chart.js to avoid SSR issues
    import('chart.js/auto').then(({ default: Chart }) => {
      const ctx = canvasRef.current.getContext('2d')
      chart = new Chart(ctx, {
        data: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              type: 'bar',
              label: 'Videos Analyzed',
              data: [120, 135, 128, 195, 160, 145, 185],
              backgroundColor: 'rgba(99,102,241,.25)',
              borderRadius: 4,
              yAxisID: 'y2',
            },
            {
              type: 'line',
              label: 'Confidence %',
              data: [86, 88, 82, 97, 83, 87, 92],
              borderColor: '#4f46e5',
              backgroundColor: 'rgba(99,102,241,.08)',
              fill: true,
              tension: 0.45,
              pointRadius: 4,
              pointBackgroundColor: '#4f46e5',
              yAxisID: 'y',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              min: 60,
              max: 100,
              position: 'left',
              grid: { color: 'rgba(0,0,0,.05)' },
              ticks: { font: { size: 12 }, color: '#94a3b8' },
            },
            y2: {
              position: 'right',
              grid: { display: false },
              ticks: { font: { size: 12 }, color: '#94a3b8' },
            },
            x: {
              grid: { display: false },
              ticks: { font: { size: 12 }, color: '#94a3b8' },
            },
          },
        },
      })
    })

    return () => {
      if (chart) chart.destroy()
    }
  }, [])

  return (
    <div style={{ position: 'relative', height: 260 }}>
      <canvas ref={canvasRef} role="img" aria-label="Detection history and confidence trends by day of week" />
    </div>
  )
}

function DonutChart() {
  const canvasRef = useRef()

  useEffect(() => {
    let chart = null

    import('chart.js/auto').then(({ default: Chart }) => {
      const ctx = canvasRef.current.getContext('2d')
      chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Real Videos', 'Fake/Manipulated'],
          datasets: [
            {
              data: [68, 32],
              backgroundColor: ['#6366f1', '#ef4444'],
              borderWidth: 0,
              hoverOffset: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '72%',
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (c) => ` ${c.label}: ${c.parsed}%`,
              },
            },
          },
        },
      })
    })

    return () => {
      if (chart) chart.destroy()
    }
  }, [])

  return (
    <div style={{ position: 'relative', height: 220 }}>
      <canvas ref={canvasRef} role="img" aria-label="Distribution: 68% real videos, 32% fake" />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--gray-900)' }}>32%</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>Fake Rate</div>
        </div>
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════
   DASHBOARD SECTION
══════════════════════════════════════════ */
const STATS = [
  {
    color: 'blue',
    icon: '🎬',
    label: 'Total Videos Analyzed',
    value: '12,450',
    change: '+12%',
    changeType: 'up',
  },
  {
    color: 'red',
    icon: '🎭',
    label: 'Fake Videos Detected',
    value: '3,892',
    change: '+5%',
    changeType: 'up',
  },
  {
    color: 'green',
    icon: '🎯',
    label: 'Model Accuracy Rate',
    value: '98.7%',
    change: 'Stable',
    changeType: 'stable',
  },
  {
    color: 'purple',
    icon: '⚡',
    label: 'Avg. Processing Time',
    value: '1.2s',
    change: '-0.2s',
    changeType: 'neg',
  },
]

function Dashboard() {
  return (
    <section id="dashboard">
      <div className="section-inner">
        <div className="dash-topbar">
          <div>
            <h2>System Analytics</h2>
            <p>Real-time performance metrics of the Spatiotemporal model.</p>
          </div>
          <a className="view-report" href="#" onClick={(e) => e.preventDefault()}>
            View Full Report
            <ExternalLinkIcon />
          </a>
        </div>

        {/* Stat cards */}
        <div className="stats-grid">
          {STATS.map((s) => (
            <div key={s.label} className={`stat-card ${s.color}`}>
              <div className="stat-card-icon">{s.icon}</div>
              <div className="stat-card-label">{s.label}</div>
              <div className="stat-card-value">{s.value}</div>
              <span
                className={`stat-card-change ${
                  s.changeType === 'up'
                    ? 'change-up'
                    : s.changeType === 'stable'
                    ? 'change-stable'
                    : 'change-neg'
                }`}
              >
                {s.changeType === 'up' ? '↑ ' : ''}{s.change}
              </span>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="charts-grid">
          <div className="chart-card">
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 20,
              }}
            >
              <h3>Detection History &amp; Confidence Trends</h3>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--gray-400)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 2,
                      background: '#6366f1',
                      display: 'inline-block',
                    }}
                  />
                  Confidence %
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 2,
                      background: 'rgba(99,102,241,.35)',
                      display: 'inline-block',
                    }}
                  />
                  Volume
                </span>
              </div>
            </div>
            <BarChart />
          </div>

          <div className="chart-card">
            <h3>Real vs Fake Distribution</h3>
            <DonutChart />
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: 24,
                marginTop: 16,
                fontSize: 13,
                color: 'var(--gray-600)',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: 3,
                    background: '#6366f1',
                    display: 'inline-block',
                  }}
                />
                Real Videos
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: 3,
                    background: '#ef4444',
                    display: 'inline-block',
                  }}
                />
                Fake/Manipulated
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ══════════════════════════════════════════
   FEATURES SECTION
══════════════════════════════════════════ */
const FEATURES = [
  {
    icon: '📐',
    bg: '#eef2ff',
    title: 'CNN Spatial Analysis',
    desc: 'Extracts frame-level spatial features to detect artifacts, blending boundaries, and unnatural textures introduced during face swapping.',
  },
  {
    icon: '⏱',
    bg: '#f5f3ff',
    title: 'Temporal Motion Tracking',
    desc: 'Analyzes sequential frames using RNN/LSTM networks to identify unnatural micro-expressions, irregular blinking rates, and temporal jitter.',
  },
  {
    icon: '👁',
    bg: '#eef2ff',
    title: 'Attention Mechanism',
    desc: 'Focuses neural network processing power on critical facial regions (eyes, mouth, borders) where manipulation artifacts are most prevalent.',
  },
  {
    icon: '⚙️',
    bg: '#f0fdf4',
    title: 'Compression Resilience',
    desc: 'Robust detection algorithms that maintain high accuracy even when videos have been heavily compressed for social media sharing.',
  },
  {
    icon: '😊',
    bg: '#f0fdf4',
    title: 'Facial Landmark Detection',
    desc: 'Maps 68+ facial keypoints to track geometric inconsistencies and unnatural deformations in 3D face alignment.',
  },
  {
    icon: '🔥',
    bg: '#fff1f2',
    title: 'Heatmap Visualization',
    desc: "Generates intuitive Class Activation Maps (CAM) to visually explain which regions influenced the model's 'fake' prediction.",
  },
]

function Features() {
  return (
    <section id="features">
      <div className="section-inner">
        <div className="section-header">
          <h2>Core Architecture</h2>
          <p>
            Our system utilizes state-of-the-art neural network topologies to detect
            minute spatiotemporal inconsistencies.
          </p>
        </div>

        <div className="features-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon" style={{ background: f.bg, fontSize: 22 }}>
                {f.icon}
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ══════════════════════════════════════════
   APP ROOT
══════════════════════════════════════════ */
export default function App() {
  const [activeSection, setActiveSection] = useState('home')

  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  useEffect(() => {
    const SECTIONS = ['home', 'upload', 'dashboard', 'features']

    const handler = () => {
      for (const id of SECTIONS) {
        const el = document.getElementById(id)
        if (!el) continue
        const rect = el.getBoundingClientRect()
        if (rect.top <= 80 && rect.bottom > 80) {
          setActiveSection(id)
          break
        }
      }
    }

    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <>
      <Navbar activeSection={activeSection} scrollTo={scrollTo} />
      <Hero scrollTo={scrollTo} />
      <UploadSection />
      <Dashboard />
      <Features />
    </>
  )
}
