import useHashRoute from './hooks/useHashRoute.js'
import Navbar from './components/Navbar.jsx'
import HomePage from './pages/HomePage.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import './App.css'

export default function App() {
  const route = useHashRoute()

  return (
    <div className="app">
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById('main')?.focus() }}>
        Skip to content
      </a>
      <Navbar route={route} />
      <main id="main" tabIndex={-1}>
        {route === '/' && <HomePage />}
        {route === '/analyze' && <AnalyzePage />}
      </main>
    </div>
  )
}
