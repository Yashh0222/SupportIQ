import { useAuth } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

export default function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { isLoaded, userId, sessionClaims } = useAuth()

  if (!isLoaded) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    )
  }

  if (!userId) {
    return <Navigate to="/sign-in" replace />
  }

  if (requireAdmin) {
    const role = (sessionClaims as Record<string, unknown> | null)?.metadata
    const metadata = role && typeof role === 'object' ? (role as Record<string, unknown>) : null
    if (metadata?.role !== 'admin') {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900">Access Denied</h2>
            <p className="mt-2 text-sm text-gray-500">
              You need admin privileges to access this page.
            </p>
          </div>
        </div>
      )
    }
  }

  return <>{children}</>
}
