import { ShieldIcon } from './Icons.jsx'

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/analyze', label: 'Analyze Video' },
]

export default function Navbar({ route }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <a className="brand" href="#/" aria-label="DeepFake Detector home">
          <span className="brand-mark">
            <ShieldIcon width={18} height={18} />
          </span>
          <span className="brand-name">DeepFake Detector</span>
        </a>
        <nav aria-label="Main">
          <ul className="nav-links">
            {LINKS.map((l) => (
              <li key={l.to}>
                <a
                  href={`#${l.to}`}
                  className={route === l.to ? 'active' : undefined}
                  aria-current={route === l.to ? 'page' : undefined}
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  )
}
