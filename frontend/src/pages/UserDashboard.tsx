import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import ChatWidget from '../widget/ChatWidget'
import {
  fetchMyCompanies,
  createCompany,
  deleteCompany,
  submitOriginRequest,
  fetchMyOriginRequests,
  uploadDocuments,
} from '../api/client'
import type { CompanyInfo, OriginRequest, UploadResult } from '../api/client'

const ACCEPTED = '.md,.txt,.rst,.html,.pdf'
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function generateEmbedHtml(companyId: string): string {
  const backendUrl = API_URL
  return `<script src="${backendUrl}/widget.js" data-company="${companyId}" data-api-url="${backendUrl}" async></script>`
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="rounded bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-200"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

export default function UserDashboard() {
  // Companies added 
  const [companies, setCompanies] = useState<CompanyInfo[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [newCompany, setNewCompany] = useState({ id: '', display_name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createdCompanyId, setCreatedCompanyId] = useState<string | null>(null)

  // Upload
  const [selectedCompany, setSelectedCompany] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadResults, setUploadResults] = useState<UploadResult[] | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Widget code
  const [showWidgetFor, setShowWidgetFor] = useState<string | null>(null)

  // Origin requests
  const [originRequests, setOriginRequests] = useState<OriginRequest[]>([])
  const [showOriginForm, setShowOriginForm] = useState<string | null>(null)
  const [originForm, setOriginForm] = useState({ origin: '', reason: '' })
  const [originSubmitting, setOriginSubmitting] = useState(false)
  const [originMessage, setOriginMessage] = useState<string | null>(null)

  const loadCompanies = useCallback(async () => {
    try {
      const list = await fetchMyCompanies()
      setCompanies(list)
      setSelectedCompany((prev) => (prev && list.some((c) => c.id === prev) ? prev : list[0]?.id ?? ''))
    } catch {
      setCompanies([])
    }
  }, [])

  const loadOriginRequests = useCallback(async () => {
    try {
      const list = await fetchMyOriginRequests()
      setOriginRequests(list)
    } catch {
      setOriginRequests([])
    }
  }, [])

  const onDeleteCompany = async (companyId: string) => {
    if (!confirm(`Delete company "${companyId}"? This cannot be undone.`)) return
    try {
      await deleteCompany(companyId)
      setSelectedCompany('')
      void loadCompanies()
      void loadOriginRequests()
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      alert(detail ?? 'Could not delete the company.')
    }
  }

  useEffect(() => {
    void loadCompanies()
    void loadOriginRequests()
  }, [loadCompanies, loadOriginRequests])

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (creating) return
    setCreating(true)
    setCreateError(null)
    try {
      const created = await createCompany(newCompany)
      setCreatedCompanyId(created.id)
      await loadCompanies()
      setSelectedCompany(created.id)
      setShowCreate(false)
      setNewCompany({ id: '', display_name: '', description: '' })
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(detail ?? 'Could not create the company.')
    } finally {
      setCreating(false)
    }
  }

  const onUpload = async (e: FormEvent) => {
    e.preventDefault()
    if (files.length === 0 || uploadState === 'uploading') return
    setUploadState('uploading')
    setUploadError(null)
    try {
      const res = await uploadDocuments(files, undefined, selectedCompany)
      setUploadResults(res.results)
      setUploadState('success')
      setFiles([])
      void loadCompanies()
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setUploadError(detail ?? 'Upload failed. Make sure the backend is running.')
      setUploadState('error')
    }
  }

  const onSubmitOrigin = async (e: FormEvent) => {
    e.preventDefault()
    if (!originForm.origin || originSubmitting) return
    setOriginSubmitting(true)
    setOriginMessage(null)
    try {
      const result = await submitOriginRequest({
        origin: originForm.origin,
        company_id: showOriginForm!,
        reason: originForm.reason,
      })
      setOriginMessage(result.message)
      setOriginForm({ origin: '', reason: '' })
      setShowOriginForm(null)
      void loadOriginRequests()
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setOriginMessage(detail ?? 'Failed to submit request.')
    } finally {
      setOriginSubmitting(false)
    }
  }

  const statusColor = (status: string) => {
    if (status === 'approved') return 'text-green-700 bg-green-50 border-green-200'
    if (status === 'rejected') return 'text-red-700 bg-red-50 border-red-200'
    return 'text-yellow-700 bg-yellow-50 border-yellow-200'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-100">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <Link to="/" className="text-lg font-bold text-gray-900">
            Support<span className="text-indigo-600">IQ</span>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/" className="text-gray-500 hover:text-gray-700">Home</Link>
            <span className="font-medium text-indigo-600">My Dashboard</span>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 pt-20 pb-14">
        <h1 className="text-3xl font-bold text-gray-900">My Dashboard</h1>
        <p className="mt-2 text-sm text-gray-500">
          Create companies, upload documents, generate widget code, and request origin access.
        </p>

        {/* ─── Create Company ─────────────────────────────────────── */}
        <div className="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">My Companies</h2>
            <button
              onClick={() => { setShowCreate(!showCreate); setCreatedCompanyId(null) }}
              className="rounded-full bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
            >
              {showCreate ? 'Cancel' : '+ Create Company'}
            </button>
          </div>

          {showCreate && (
            <form onSubmit={onCreate} className="mt-4 space-y-3 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4">
              <input
                value={newCompany.id}
                onChange={(e) => setNewCompany({ ...newCompany, id: e.target.value.toLowerCase() })}
                placeholder="Company id (e.g. mycompany)"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
              />
              <input
                value={newCompany.display_name}
                onChange={(e) => setNewCompany({ ...newCompany, display_name: e.target.value })}
                placeholder="Display name (e.g. My Company)"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
              />
              <input
                value={newCompany.description}
                onChange={(e) => setNewCompany({ ...newCompany, description: e.target.value })}
                placeholder="Short description (optional)"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
              />
              {createError && <p className="text-xs text-red-600">{createError}</p>}
              <button
                type="submit"
                disabled={creating || !newCompany.id || !newCompany.display_name}
                className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {creating ? 'Creating...' : 'Create Company'}
              </button>
            </form>
          )}

          {createdCompanyId && (
            <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="text-sm font-medium text-green-800">
                Company <span className="font-bold">{createdCompanyId}</span> created!
              </p>
              <p className="mt-1 text-xs text-green-600">
                Upload documents below, then get the widget embed code to add to your site.
              </p>
            </div>
          )}

          {companies.length === 0 ? (
            <p className="mt-4 text-sm text-gray-400">No companies yet. Create one to get started!</p>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {companies.map((c) => (
                <div
                  key={c.id}
                  className={`rounded-xl border p-4 transition ${
                    selectedCompany === c.id
                      ? 'border-indigo-400 bg-indigo-50 ring-1 ring-indigo-300'
                      : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <div
                    className="cursor-pointer"
                    onClick={() => setSelectedCompany(c.id)}
                  >
                    <h3 className="font-semibold text-gray-900">{c.display_name}</h3>
                    <p className="mt-0.5 text-xs text-gray-500">{c.id}</p>
                    {c.description && (
                      <p className="mt-1 text-xs text-gray-600">{c.description}</p>
                    )}
                    <p className="mt-1 text-xs font-medium text-indigo-600">{c.doc_count} documents</p>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => setShowWidgetFor(showWidgetFor === c.id ? null : c.id)}
                      className="rounded bg-indigo-100 px-2 py-1 text-[10px] font-semibold text-indigo-700 hover:bg-indigo-200"
                    >
                      Widget Code
                    </button>
                    <button
                      onClick={() => setShowOriginForm(showOriginForm === c.id ? null : c.id)}
                      className="rounded bg-gray-100 px-2 py-1 text-[10px] font-semibold text-gray-600 hover:bg-gray-200"
                    >
                      Request Origin
                    </button>
                    <button
                      onClick={() => void onDeleteCompany(c.id)}
                      className="rounded bg-red-50 px-2 py-1 text-[10px] font-semibold text-red-600 hover:bg-red-100"
                    >
                      Delete
                    </button>
                  </div>

                  {/* Widget code display */}
                  {showWidgetFor === c.id && (
                    <div className="mt-3 rounded-lg bg-gray-900 p-3">
                      <p className="mb-1 text-[10px] font-semibold text-gray-400">Embed HTML:</p>
                      <pre className="overflow-x-auto text-[10px] text-green-400">
                        {generateEmbedHtml(c.id)}
                      </pre>
                      <div className="mt-2 flex gap-2">
                        <CopyButton text={generateEmbedHtml(c.id)} />
                      </div>
                      <p className="mt-2 text-[10px] text-gray-500">
                        Paste this into your website's HTML where you want the chat widget to appear.
                      </p>
                    </div>
                  )}

                  {/* Origin request form */}
                  {showOriginForm === c.id && (
                    <div className="mt-3 rounded-lg border border-gray-200 bg-white p-3">
                      <p className="text-xs font-semibold text-gray-700">Request Origin Access</p>
                      <p className="mt-0.5 text-[10px] text-gray-500">
                        Submit your site origin. An admin will review and approve it.
                      </p>
                      <form onSubmit={onSubmitOrigin} className="mt-2 space-y-2">
                        <input
                          value={originForm.origin}
                          onChange={(e) => setOriginForm({ ...originForm, origin: e.target.value })}
                          placeholder="https://your-site.com"
                          className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-indigo-500"
                        />
                        <input
                          value={originForm.reason}
                          onChange={(e) => setOriginForm({ ...originForm, reason: e.target.value })}
                          placeholder="Reason (optional)"
                          className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-indigo-500"
                        />
                        <button
                          type="submit"
                          disabled={originSubmitting || !originForm.origin}
                          className="w-full rounded bg-indigo-600 px-2 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                        >
                          {originSubmitting ? 'Submitting...' : 'Submit Request'}
                        </button>
                      </form>
                      {originMessage && (
                        <p className="mt-2 text-xs text-green-700">{originMessage}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ─── Upload Documents ────────────────────────────────────── */}
        {companies.length > 0 && (
          <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Upload Documents</h2>
            <p className="mt-1 text-sm text-gray-500">
              Add documents to your selected company&apos;s knowledge base.
            </p>

            <div className="mt-3">
              <label className="text-xs font-semibold uppercase text-gray-400">Company</label>
              <select
                value={selectedCompany}
                onChange={(e) => setSelectedCompany(e.target.value)}
                className="mt-1 w-full rounded-full border border-gray-300 px-3.5 py-2 text-sm outline-none focus:border-indigo-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.display_name} ({c.id}) - {c.doc_count} docs
                  </option>
                ))}
              </select>
            </div>

            <form onSubmit={onUpload} className="mt-4 space-y-3">
              <input
                type="file"
                multiple
                accept={ACCEPTED}
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                className="block w-full text-sm text-gray-700 file:mr-3 file:rounded-full file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100"
              />
              <button
                type="submit"
                disabled={files.length === 0 || uploadState === 'uploading'}
                className="w-full rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {uploadState === 'uploading'
                  ? 'Uploading...'
                  : `Upload ${files.length === 0 ? 'document(s)' : `${files.length} document${files.length === 1 ? '' : 's'}`}`}
              </button>
            </form>

            {uploadState === 'success' && uploadResults && (
              <div className="mt-3 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                Ingested {uploadResults.length} document(s) ({uploadResults.reduce((n, r) => n + r.chunks_added, 0)} chunks)
              </div>
            )}
            {uploadState === 'error' && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {uploadError}
              </div>
            )}
          </div>
        )}

        {/* ─── My Origin Requests ─────────────────────────────────── */}
        {originRequests.length > 0 && (
          <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">My Origin Requests</h2>
            <p className="mt-1 text-sm text-gray-500">
              Track the status of your submitted origin access requests.
            </p>
            <div className="mt-4 space-y-2">
              {originRequests.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{r.origin}</p>
                    <p className="text-xs text-gray-500">Company: {r.company_id}</p>
                    {r.reason && <p className="text-xs text-gray-400">Reason: {r.reason}</p>}
                  </div>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusColor(r.status)}`}>
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── Chat Demo ──────────────────────────────────────────── */}
        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-indigo-500 hover:text-indigo-700">
            Back to Home
          </Link>
        </div>
      </div>

      {selectedCompany && (
        <ChatWidget
          apiUrl={API_URL}
          org={companies.find((c) => c.id === selectedCompany)?.display_name}
          company={selectedCompany}
        />
      )}
    </div>
  )
}
