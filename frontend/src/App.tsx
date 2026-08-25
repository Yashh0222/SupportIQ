import { useAuth } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import UploadPanel from './admin/UploadPanel'

export default function App({ onBack }: { onBack?: () => void }) {
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

  const role = (sessionClaims as Record<string, unknown> | null)?.metadata
  const metadata = role && typeof role === 'object' ? (role as Record<string, unknown>) : null
  if (metadata?.role !== 'admin') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">Admin Access Required</h2>
          <p className="mt-2 text-sm text-gray-500">
            You need admin privileges to access this page.
          </p>
          <a
            href="/"
            className="mt-4 inline-block rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            Back to Home
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-gradient-to-br from-indigo-50 to-white px-6 py-12 text-center">
      {onBack && (
        <button
          onClick={onBack}
          className="mb-4 rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
        >
          ← Back to demo
        </button>
      )}
      <h1 className="text-4xl font-bold text-gray-900">SupportIQ</h1>
      <p className="mt-3 max-w-md text-gray-600">
        Agentic RAG customer support. Click the chat bubble in the bottom-right
        corner to ask a question about AcmeCRM..
      </p>
      <div className="mt-6 rounded-xl border border-indigo-200 bg-white px-4 py-2 text-sm text-indigo-700">
        Try: &quot;What is the refund window?&quot;
      </div>
      <UploadPanel />
    </div>
  )
}
