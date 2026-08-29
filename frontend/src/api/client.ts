// Added axios
// Modified existing and configured axios with types and interfaces for api
import axios from 'axios'
import { useAuth } from '@clerk/clerk-react'

export interface ToolCall {
  name: string
  arguments: Record<string, string>
}

export interface Trace {
  intent: string
  retrieved_chunks: string[]
  grading: string
  reformulated_query: string | null
  escalated: boolean
  tool_calls: ToolCall[]
  tool_result: string | null
}

export interface ChatResponse {
  answer: string
  sources: string[]
  trace: Trace
}

export interface ChatRequest {
  message: string
  conversation_id: string
  company?: string
}

export interface CompanyInfo {
  id: string
  display_name: string
  description: string
  doc_count: number
  owner_id?: string
}

export interface CreateCompanyRequest {
  id: string
  display_name: string
  description: string
}

export interface UploadResult {
  filename: string
  chunks_added: number
}

export interface UploadResponse {
  company: string
  files: number
  chunks_added: number
  results: UploadResult[]
}

export interface OriginRequest {
  id: string
  user_id: string
  user_email: string
  company_id: string
  origin: string
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: number
  resolved_at: number
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Axios instance that attaches the Clerk session token to every request
const api = axios.create({
  baseURL: API_URL,
})

// Hook-based token provider — must be used inside a React component or via a setter
let tokenProvider: (() => Promise<string | null>) | null = null

export function setTokenProvider(provider: () => Promise<string | null>) {
  tokenProvider = provider
}

api.interceptors.request.use(async (config) => {
  if (tokenProvider) {
    const token = await tokenProvider()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

export function useApiSetup() {
  const { getToken } = useAuth()
  setTokenProvider(getToken)
}

// ─── Chat (public) ──────────────────────────────────────────────────

export async function sendMessage(
  message: string,
  conversationId: string,
  _apiUrl?: string,
  company?: string,
): Promise<ChatResponse> {
  const { data } = await axios.post<ChatResponse>(`${API_URL}/chat`, {
    message,
    conversation_id: conversationId,
    company,
  } satisfies ChatRequest)
  return data
}

// ─── Caching ────────────────────────────────────────────────────────
// Module-level in-memory cache so navigating pages doesn't re-fetch the
// same data on every mount. `force` bypasses the cache for fresh reads.

const CACHE_TTL_MS = 30_000

function createCached<T>(fetcher: () => Promise<T>) {
  let value: T | null = null
  let expires = 0
  let inFlight: Promise<T> | null = null

  async function get(force = false): Promise<T> {
    const now = Date.now()
    if (!force && value !== null && now < expires) return value
    if (inFlight) return inFlight
    inFlight = fetcher()
      .then((data) => {
        value = data
        expires = now + CACHE_TTL_MS
        return data
      })
      .finally(() => {
        inFlight = null
      })
    return inFlight
  }

  function invalidate() {
    value = null
    expires = 0
  }

  return { get, invalidate }
}

// ─── Companies (authenticated) ──────────────────────────────────────

const companiesCache = createCached<CompanyInfo[]>(async () => {
  const { data } = await api.get<CompanyInfo[]>('/companies')
  return data
})
const myCompaniesCache = createCached<CompanyInfo[]>(async () => {
  const { data } = await api.get<CompanyInfo[]>('/companies/mine')
  return data
})

export async function fetchCompanies(_apiUrl?: string, force = false): Promise<CompanyInfo[]> {
  return companiesCache.get(force)
}

export async function fetchMyCompanies(force = false): Promise<CompanyInfo[]> {
  return myCompaniesCache.get(force)
}

export function invalidateCompaniesCache() {
  companiesCache.invalidate()
  myCompaniesCache.invalidate()
}

export async function createCompany(
  payload: CreateCompanyRequest,
  _apiUrl?: string,
): Promise<CompanyInfo> {
  const { data } = await api.post<CompanyInfo>('/companies', payload)
  return data
}

export async function deleteCompany(companyId: string): Promise<void> {
  await api.delete(`/companies/${encodeURIComponent(companyId)}`)
}

// ─── Upload (authenticated, owner or admin) ─────────────────────────

export async function uploadDocuments(
  files: File[],
  _apiUrl?: string,
  company?: string,
): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  if (company) formData.append('company', company)
  const { data } = await api.post<UploadResponse>('/upload', formData)
  return data
}

// ─── Origin requests (authenticated user) ──────────────────────────

export async function submitOriginRequest(payload: {
  origin: string
  company_id: string
  reason?: string
}): Promise<{ id: string; status: string; message: string }> {
  const { data } = await api.post('/origin-requests', payload)
  return data
}

export async function fetchMyOriginRequests(): Promise<OriginRequest[]> {
  const { data } = await api.get<OriginRequest[]>('/origin-requests/mine')
  return data
}

// ─── Origins (admin) ───────────────────────────────────────────────

export async function fetchAllowedOrigins(_apiUrl?: string): Promise<string[]> {
  const { data } = await api.get<{ origins: string[] }>('/origins')
  return data.origins
}

export async function addAllowedOrigin(
  origin: string,
  _apiUrl?: string,
): Promise<string[]> {
  const { data } = await api.post<{ origins: string[] }>('/origins', { origin })
  return data.origins
}

export async function removeAllowedOrigin(
  origin: string,
  _apiUrl?: string,
): Promise<string[]> {
  const { data } = await api.delete<{ origins: string[] }>(
    `/origins/${encodeURIComponent(origin)}`,
  )
  return data.origins
}

// ─── Admin: origin request management ──────────────────────────────

export async function fetchAllOriginRequests(
  status?: string,
): Promise<OriginRequest[]> {
  const params = status ? { status } : {}
  const { data } = await api.get<OriginRequest[]>('/admin/origin-requests', { params })
  return data
}

export async function approveOriginRequest(
  requestId: string,
): Promise<{ message: string }> {
  const { data } = await api.post(`/admin/origin-requests/${requestId}/approve`)
  return data
}

export async function rejectOriginRequest(
  requestId: string,
): Promise<{ message: string }> {
  const { data } = await api.post(`/admin/origin-requests/${requestId}/reject`)
  return data
}
