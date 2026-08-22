// Added axios
import axios from 'axios'

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
  const { data } = await axios.post<UploadResponse>(`${apiUrl ?? API_URL}/upload`, formData)
  return data
}

export async function fetchCompanies(apiUrl?: string): Promise<CompanyInfo[]> {
  const { data } = await axios.get<CompanyInfo[]>(`${apiUrl ?? API_URL}/companies`)
  return data
}

export async function createCompany(
  payload: CreateCompanyRequest,
  apiUrl?: string,
): Promise<CompanyInfo> {
  const { data } = await axios.post<CompanyInfo>(
    `${apiUrl ?? API_URL}/companies`,
    payload,
  )
  return data
}

export async function fetchAllowedOrigins(apiUrl?: string): Promise<string[]> {
  const { data } = await axios.get<{ origins: string[] }>(
    `${apiUrl ?? API_URL}/origins`,
  )
  return data.origins
}

export async function addAllowedOrigin(
  origin: string,
  apiUrl?: string,
): Promise<string[]> {
  const { data } = await axios.post<{ origins: string[] }>(
    `${apiUrl ?? API_URL}/origins`,
    { origin },
  )
  return data.origins
}

export async function removeAllowedOrigin(
  origin: string,
  apiUrl?: string,
): Promise<string[]> {
  const { data } = await axios.delete<{ origins: string[] }>(
    `${apiUrl ?? API_URL}/origins/${encodeURIComponent(origin)}`,
  )
  return data.origins
}
