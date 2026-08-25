import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import {
  addAllowedOrigin,
  fetchAllowedOrigins,
  fetchAllOriginRequests,
  fetchCompanies,
  approveOriginRequest,
  rejectOriginRequest,
  removeAllowedOrigin,
  deleteCompany,
} from './api/client'
import type { CompanyInfo, OriginRequest } from './api/client'

export default function App({ onBack }: { onBack?: () => void }) {
  const { isLoaded, userId, sessionClaims } = useAuth()

  const [origins, setOrigins] = useState<string[]>([])
  const [newOrigin, setNewOrigin] = useState('')
  const [originError, setOriginError] = useState<string | null>(null)
  const [originBusy, setOriginBusy] = useState(false)

  const [requests, setRequests] = useState<OriginRequest[]>([])
  const [requestFilter, setRequestFilter] = useState<string>('pending')
  const [actionBusy, setActionBusy] = useState<string | null>(null)

  const [allCompanies, setAllCompanies] = useState<CompanyInfo[]>([])

  const loadOrigins = useCallback(async () => {
    try { setOrigins(await fetchAllowedOrigins()) } catch { setOrigins([]) }
  }, [])

  const loadRequests = useCallback(async () => {
    try { setRequests(await fetchAllOriginRequests(requestFilter || undefined)) } catch { setRequests([]) }
  }, [requestFilter])

  useEffect(() => { void loadOrigins() }, [loadOrigins])
  useEffect(() => { void loadRequests() }, [loadRequests])

  const loadCompanies = useCallback(async () => {
    try { setAllCompanies(await fetchCompanies()) } catch { setAllCompanies([]) }
  }, [])

  useEffect(() => { void loadCompanies() }, [loadCompanies])

  const onAddOrigin = async (e: FormEvent) => {
    e.preventDefault()
    if (!newOrigin || originBusy) return
    setOriginBusy(true)
    setOriginError(null)
    try {
      setOrigins(await addAllowedOrigin(newOrigin))
      setNewOrigin('')
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setOriginError(detail ?? 'Could not add the origin.')
    } finally {
      setOriginBusy(false)
    }
  }

  const onRemoveOrigin = async (origin: string) => {
    if (originBusy) return
    setOriginBusy(true)
    setOriginError(null)
    try {
      setOrigins(await removeAllowedOrigin(origin))
    } catch {
      setOriginError('Could not remove the origin.')
    } finally {
      setOriginBusy(false)
    }
  }

  const onApprove = async (requestId: string) => {
    setActionBusy(requestId)
    try {
      await approveOriginRequest(requestId)
      void loadRequests()
      void loadOrigins()
    } catch { /* ignore */ }
    setActionBusy(null)
  }

  const onReject = async (requestId: string) => {
    setActionBusy(requestId)
    try {
      await rejectOriginRequest(requestId)
      void loadRequests()
    } catch { /* ignore */ }
    setActionBusy(null)
  }

  const onDeleteCompany = async (companyId: string) => {
    if (!confirm(`Delete company "${companyId}"? This will remove all its documents and data.`)) return
    try {
      await deleteCompany(companyId)
      void loadCompanies()
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      alert(detail ?? 'Could not delete the company.')
    }
  }

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
          <p className="mt-2 text-sm text-gray-500">You need admin privileges to access this page.</p>
          <a href="/" className="mt-4 inline-block rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Back to Home</a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-gradient-to-br from-indigo-50 to-white px-6 py-12 text-center">
      {onBack && (
        <button onClick={onBack} className="mb-4 rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50">
          Back to demo
        </button>
      )}
      <h1 className="text-4xl font-bold text-gray-900">SupportIQ <span className="text-sm font-normal text-gray-400">Admin Panel</span></h1>

      {/* ─── Pending Origin Requests ─────────────────────────────── */}
      <div className="mt-8 w-full max-w-2xl rounded-2xl border border-yellow-200 bg-white p-6 text-left shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Origin Approval Requests</h2>
        <p className="mt-1 text-sm text-gray-500">Review and approve user requests to add their site origins.</p>

        <div className="mt-3 flex gap-2">
          {['pending', 'approved', 'rejected', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setRequestFilter(f)}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                requestFilter === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {requests.length === 0 ? (
          <p className="mt-4 text-sm text-gray-400">No requests found.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {requests.map((r) => (
              <div key={r.id} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{r.origin}</p>
                    <p className="text-xs text-gray-500">Company: {r.company_id} | By: {r.user_email || r.user_id}</p>
                    {r.reason && <p className="mt-1 text-xs text-gray-400">Reason: {r.reason}</p>}
                    <span className={`mt-1 inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                      r.status === 'approved' ? 'text-green-700 bg-green-50 border-green-200'
                        : r.status === 'rejected' ? 'text-red-700 bg-red-50 border-red-200'
                        : 'text-yellow-700 bg-yellow-50 border-yellow-200'
                    }`}>
                      {r.status}
                    </span>
                  </div>
                  {r.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => void onApprove(r.id)}
                        disabled={actionBusy === r.id}
                        className="rounded bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        {actionBusy === r.id ? '...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => void onReject(r.id)}
                        disabled={actionBusy === r.id}
                        className="rounded bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        {actionBusy === r.id ? '...' : 'Reject'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── All Companies ──────────────────────────────────────── */}
      <div className="mt-6 w-full max-w-2xl rounded-2xl border border-indigo-200 bg-white p-6 text-left shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">All Companies</h2>
        <p className="mt-1 text-sm text-gray-500">Manage and delete any company in the system.</p>
        {allCompanies.length === 0 ? (
          <p className="mt-4 text-sm text-gray-400">No companies found.</p>
        ) : (
          <div className="mt-4 space-y-2">
            {allCompanies.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{c.display_name} <span className="font-normal text-gray-400">({c.id})</span></p>
                  {c.description && <p className="text-xs text-gray-500">{c.description}</p>}
                  <p className="text-xs text-gray-400">{c.doc_count} documents</p>
                </div>
                <button
                  onClick={() => void onDeleteCompany(c.id)}
                  className="shrink-0 rounded bg-red-50 px-3 py-1 text-xs font-semibold text-red-600 hover:bg-red-100"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── Direct Origin Management ─────────────────────────────── */}
      <div className="mt-6 w-full max-w-2xl rounded-2xl border border-indigo-200 bg-white p-6 text-left shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Direct Origin Management</h2>
        <p className="mt-1 text-sm text-gray-500">Add or remove allowed origins directly.</p>

        <ul className="mt-3 space-y-1">
          {origins.map((o) => (
            <li key={o} className="flex items-center justify-between rounded-lg bg-indigo-50/60 px-3 py-1.5 text-xs text-gray-700">
              <span className="truncate font-mono">{o}</span>
              <button type="button" onClick={() => void onRemoveOrigin(o)} disabled={originBusy} className="ml-2 shrink-0 font-semibold text-red-500 hover:text-red-700 disabled:opacity-50">Remove</button>
            </li>
          ))}
          {origins.length === 0 && <li className="text-xs text-gray-400">No origins yet.</li>}
        </ul>

        <form onSubmit={onAddOrigin} className="mt-3 flex gap-2">
          <input value={newOrigin} onChange={(e) => setNewOrigin(e.target.value)} placeholder="https://your-site.com" className="flex-1 rounded-full border border-gray-300 px-3 py-1.5 text-xs outline-none focus:border-indigo-500" />
          <button type="submit" disabled={!newOrigin || originBusy} className="rounded-full bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">Add origin</button>
        </form>
        {originError && <p className="mt-1 text-xs text-red-600">{originError}</p>}
      </div>
    </div>
  )
}
