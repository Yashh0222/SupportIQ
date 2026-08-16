import type { Trace } from '../api/client'

export interface ChatMessage {
  id: string
  role: 'user' | 'bot'
  content: string
  sources?: string[]
  trace?: Trace
}
