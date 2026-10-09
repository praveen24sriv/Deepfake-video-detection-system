import { useEffect, useState } from 'react'

export const ROUTES = ['/', '/analyze']

function currentRoute() {
  const path = window.location.hash.replace(/^#/, '') || '/'
  return ROUTES.includes(path) ? path : '/'
}

/** Minimal hash router (React Router is not a dependency of this project). */
export default function useHashRoute() {
  const [route, setRoute] = useState(currentRoute)

  useEffect(() => {
    const onChange = () => {
      setRoute(currentRoute())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return route
}
