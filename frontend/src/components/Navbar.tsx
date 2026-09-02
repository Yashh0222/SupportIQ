import { SignedIn, SignedOut, UserButton, useAuth } from '@clerk/clerk-react'
import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { sessionClaims } = useAuth()
  const location = useLocation()

  const role = (sessionClaims as Record<string, unknown> | null)?.metadata
  const metadata = role && typeof role === 'object' ? (role as Record<string, unknown>) : null
  const isAdmin = metadata?.role === 'admin'

  const isActive = (path: string) => location.pathname === path

  const linkClass = (path: string) =>
    `rounded-full border px-4 py-1.5 text-xs font-medium transition ${
      isActive(path)
        ? 'border-indigo-300 bg-indigo-50 text-indigo-700'
        : 'border-gray-200 text-gray-500 hover:bg-gray-50'
    }`

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/" className="text-lg font-bold text-gray-900">
          Support<span className="text-indigo-600">IQ</span>
        </Link>
        <div className="flex items-center gap-2">
          <Link to="/" className={linkClass('/')}>Home</Link>
          <SignedIn>
            <Link to="/dashboard" className={linkClass('/dashboard')}>Dashboard</Link>
            {isAdmin && (
              <Link to="/admin" className={linkClass('/admin')}>Admin</Link>
            )}
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
          <SignedOut>
            <Link to="/sign-in" className={linkClass('/sign-in')}>Sign In</Link>
            <Link to="/sign-up" className="rounded-full bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700">Sign Up</Link>
          </SignedOut>
        </div>
      </div>
    </nav>
  )
}
