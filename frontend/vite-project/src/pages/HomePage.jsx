import { FilmIcon, ImageIcon, ScanIcon } from '../components/Icons.jsx'

const FEATURES = [
  {
    icon: <FilmIcon />,
    title: 'Video Analysis',
    text: 'Upload an MP4, AVI or MOV file and send it through the analysis pipeline.',
  },
  {
    icon: <ScanIcon />,
    title: 'Frame-Level Inspection',
    text: 'Frames are sampled across the video, then faces are located and checked for quality.',
  },
  {
    icon: <ImageIcon />,
    title: 'Visual Explanations',
    text: 'A visualization of an analyzed frame is returned when available. Right now it is a development overlay.',
  },
]

const STEPS = [
  'Upload a video.',
  'Process and inspect video frames.',
  'Review the available analysis results.',
]

function HeroIllustration() {
  return (
    <svg className="hero-art" viewBox="0 0 320 220" role="img" aria-label="Illustration of a video frame with a detected face region">
      <rect x="8" y="8" width="304" height="204" rx="16" fill="#fff" stroke="#e2e8f0" strokeWidth="2" />
      <rect x="24" y="24" width="272" height="140" rx="10" fill="#eef2ff" />
      <circle cx="160" cy="84" r="28" fill="#c7d2fe" />
      <path d="M104 164c4-30 28-44 56-44s52 14 56 44" fill="#c7d2fe" />
      <path d="M118 52v-12h12M202 52v-12h-12M118 116v12h12M202 116v12h-12" fill="none" stroke="#4f46e5" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="24" y="180" width="272" height="6" rx="3" fill="#e2e8f0" />
      <rect x="24" y="180" width="96" height="6" rx="3" fill="#4f46e5" />
    </svg>
  )
}

export default function HomePage() {
  const scrollToHow = () =>
    document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div className="hero-copy">
            <h1>Detect Potential Deepfake Videos</h1>
            <p className="lead">
              Analyze a video for potential signs of manipulation using our video-analysis pipeline.
            </p>
            <div className="hero-actions">
              <a className="btn btn-primary" href="#/analyze">
                Analyze a Video
              </a>
              <button type="button" className="btn btn-secondary" onClick={scrollToHow}>
                Learn How It Works
              </button>
            </div>
          </div>
          <HeroIllustration />
        </div>
      </section>

      <section className="container section" aria-label="Features">
        <div className="grid-3">
          {FEATURES.map((f) => (
            <article className="card feature" key={f.title}>
              <span className="feature-icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="container section">
        <h2 className="section-title">How it works</h2>
        <ol className="steps">
          {STEPS.map((s, i) => (
            <li key={s} className="card step">
              <span className="step-num">{i + 1}</span>
              <p>{s}</p>
            </li>
          ))}
        </ol>
      </section>
    </>
  )
}
