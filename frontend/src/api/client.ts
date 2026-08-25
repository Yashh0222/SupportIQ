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

export async function sendMessage(
  message: string,
  conversationId: string,
  apiUrl?: string,
  company?: string,
): Promise<ChatResponse> {
  const { data } = await axios.post<ChatResponse>(`${apiUrl ?? API_URL}/chat`, {
    message,
    conversation_id: conversationId,
    company,
  } satisfies ChatRequest)
  return data
}

export async function uploadDocuments(
  files: File[],
  apiUrl?: string,
  company?: string,
): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  if (company) formData.append('company', company)
  const { data } = await api.post<UploadResponse>('/upload', formData)
  return data
}

export async function fetchCompanies(apiUrl?: string): Promise<CompanyInfo[]> {
  const { data } = await api.get<CompanyInfo[]>('/companies')
  return data
}

export async function createCompany(
  payload: CreateCompanyRequest,
  apiUrl?: string,
): Promise<CompanyInfo> {
  const { data } = await api.post<CompanyInfo>('/companies', payload)
  return data
}

export async function fetchAllowedOrigins(apiUrl?: string): Promise<string[]> {
  const { data } = await api.get<{ origins: string[] }>('/origins')
  return data.origins
}

export async function addAllowedOrigin(
  origin: string,
  apiUrl?: string,
): Promise<string[]> {
  const { data } = await api.post<{ origins: string[] }>('/origins', { origin })
  return data.origins
}

export async function removeAllowedOrigin(
  origin: string,
  apiUrl?: string,
): Promise<string[]> {
  const { data } = await api.delete<{ origins: string[] }>(
    `/origins/${encodeURIComponent(origin)}`,
  )
  return data.origins
}
