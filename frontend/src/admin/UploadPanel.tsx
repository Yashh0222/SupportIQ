import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createCompany,
  fetchCompanies,
  uploadDocuments,
} from '../api/client'
import type { CompanyInfo, UploadResult } from '../api/client'

type UploadState =
  | { status: 'idle' }
  | { status: 'uploading' }
  | { status: 'success'; results: UploadResult[] }
  | { status: 'error'; message: string }

const ACCEPTED = '.md,.txt,.rst,.html,.pdf'
const DEFAULT_COMPANY = 'acmecrm'

export default function UploadPanel() {
  const [companies, setCompanies] = useState<CompanyInfo[]>([])
  const [selected, setSelected] = useState(DEFAULT_COMPANY)
  const [files, setFiles] = useState<File[]>([])
  const [state, setState] = useState<UploadState>({ status: 'idle' })

  const [showCreate, setShowCreate] = useState(false)
  const [newCompany, setNewCompany] = useState({ id: '', display_name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const formRef = useRef<HTMLFormElement>(null)

  const loadCompanies = useCallback(async () => {
    try {
      const list = await fetchCompanies()
      setCompanies(list)
      setSelected((prev) => (list.some((c) => c.id === prev) ? prev : list[0]?.id ?? DEFAULT_COMPANY))
    } catch {
      setCompanies([])
    }
  }, [])

  useEffect(() => {
    void loadCompanies()
  }, [loadCompanies])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (files.length === 0 || state.status === 'uploading') return
    setState({ status: 'uploading' })
    try {
      const res = await uploadDocuments(files, undefined, selected)
      setState({ status: 'success', results: res.results })
      formRef.current?.reset()
      setFiles([])
      void loadCompanies()
    } catch {
      setState({
        status: 'error',
        message: 'Upload failed. Make sure the backend is running, then try again.',
      })
    }
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (creating) return
    setCreating(true)
    setCreateError(null)
    try {
      const created = await createCompany(newCompany)
      await loadCompanies()
      setSelected(created.id)
      setShowCreate(false)
      setNewCompany({ id: '', display_name: '', description: '' })
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(detail ?? 'Could not create the company.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto mt-8 w-full max-w-md rounded-2xl border border-indigo-200 bg-white p-6 text-left shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Knowledge base upload</h2>
      <p className="mt-1 text-sm text-gray-500">
        Add one or more documents to any company&apos;s vector store, then ask the chat about them.
      </p>

      <div className="mt-4">
        <label className="text-xs font-semibold uppercase text-gray-400">Company</label>
        <div className="mt-1 flex items-center gap-2">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="flex-1 rounded-full border border-gray-300 px-3.5 py-2 text-sm outline-none focus:border-indigo-500"
          >
            {companies.length === 0 && <option value={DEFAULT_COMPANY}>AcmeCRM (default)</option>}
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.display_name} ({c.id}) — {c.doc_count} docs
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            className="whitespace-nowrap rounded-full border border-indigo-300 px-3 py-2 text-xs font-semibold text-indigo-600 hover:bg-indigo-50"
          >
            {showCreate ? 'Cancel' : '+ New company'}
          </button>
        </div>
      </div>

      {showCreate && (
        <form onSubmit={onCreate} className="mt-3 space-y-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-3">
          <input
            value={newCompany.id}
            onChange={(e) => setNewCompany({ ...newCompany, id: e.target.value.toLowerCase() })}
            placeholder="Company id (e.g. acmeai)"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
          />
          <input
            value={newCompany.display_name}
            onChange={(e) => setNewCompany({ ...newCompany, display_name: e.target.value })}
            placeholder="Display name (e.g. Acme AI)"
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
            {creating ? 'Creating…' : 'Create company'}
          </button>
        </form>
      )}

      <form ref={formRef} onSubmit={onSubmit} className="mt-4 space-y-3">
        <input
          type="file"
          multiple
          accept={ACCEPTED}
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          className="block w-full text-sm text-gray-700 file:mr-3 file:rounded-full file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100"
        />
        <button
          type="submit"
          disabled={files.length === 0 || state.status === 'uploading'}
          className="w-full rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {state.status === 'uploading'
            ? 'Uploading…'
            : `Upload ${files.length === 0 ? 'document(s)' : `${files.length} document${files.length === 1 ? '' : 's'}`}`}
        </button>
      </form>

      {state.status === 'success' && (
        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          {state.results.length === 1
            ? `Added ${state.results[0].filename} — ${state.results[0].chunks_added} chunk${state.results[0].chunks_added === 1 ? '' : 's'} ingested.`
            : `Ingested ${state.results.length} documents (${state.results.reduce((n, r) => n + r.chunks_added, 0)} chunks):`}
          <ul className="mt-1 list-disc pl-4">
            {state.results.map((r) => (
              <li key={r.filename}>
                {r.filename} — {r.chunks_added} chunk{r.chunks_added === 1 ? '' : 's'}
              </li>
            ))}
          </ul>
        </div>
      )}
      {state.status === 'error' && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {state.message}
        </div>
      )}

      <p className="mt-4 text-xs text-gray-400">
        Supported formats: markdown, plain text, HTML, PDF.
      </p>
    </div>
  )
}
