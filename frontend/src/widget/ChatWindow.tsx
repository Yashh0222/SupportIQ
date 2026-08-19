import { useEffect, useReducer, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { sendMessage } from '../api/client'
import { uid } from './id'
import type { ChatMessage } from './types'
import EscalationBanner from './EscalationBanner'
import MessageBubble from './MessageBubble'
import TracePanel from './TracePanel'
import TypingIndicator from './TypingIndicator'

// updated chat window 
interface ChatState {
  messages: ChatMessage[]
  loading: boolean
}

type ChatAction =
  | { type: 'add'; message: ChatMessage }
  | { type: 'loading'; loading: boolean }

function reducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'add':
      return { ...state, messages: [...state.messages, action.message] }
    case 'loading':
      return { ...state, loading: action.loading }
    default:
      return state
  }
}

export default function ChatWindow({
  conversationId,
  apiUrl,
  org,
  company,
}: {
  conversationId: string
  apiUrl?: string
  org?: string
  company?: string
}) {
  const [state, dispatch] = useReducer(reducer, { messages: [], loading: false })
  const [input, setInput] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [state.messages, state.loading])

  const appendBot = (message: Omit<ChatMessage, 'id' | 'role'>) => {
    dispatch({ type: 'add', message: { ...message, id: uid(), role: 'bot' } })
    dispatch({ type: 'loading', loading: false })
  }

  const send = async () => {
    const text = input.trim()
    if (!text || state.loading) return
    setInput('')
    dispatch({ type: 'add', message: { id: uid(), role: 'user', content: text } })
    dispatch({ type: 'loading', loading: true })
    try {
      const res = await sendMessage(text, conversationId, apiUrl, company)
      appendBot({
        content: res.answer,
        sources: res.sources,
        trace: res.trace,
      })
    } catch {
      appendBot({ content: 'Sorry, something went wrong contacting the server.' })
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    void send()
  }

  const lastBot = [...state.messages].reverse().find((m) => m.role === 'bot')
  const escalated = lastBot?.trace?.escalated === true

  return (
    <div style={{ display: 'flex', height: 'min(560px, calc(100dvh - 100px))', width: 'min(380px, calc(100vw - 24px))', flexDirection: 'column', overflow: 'hidden', borderRadius: '16px', border: '1px solid #e5e7eb', backgroundColor: '#f9fafb', boxShadow: '0 8px 30px rgba(0,0,0,0.15)', fontFamily: 'system-ui, -apple-system, sans-serif', fontSize: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#4f46e5', padding: '12px 16px', color: '#fff' }}>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600 }}>SupportIQ</div>
          <div style={{ fontSize: '11px', color: '#c7d2fe' }}>
            {org ? `AI support for ${org}` : 'AI support assistant'}
          </div>
        </div>
      </div>

      <div ref={listRef} style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {state.messages.map((message) => (
          <div key={message.id}>
            <MessageBubble message={message} />
            {message.role === 'bot' && message.trace && <TracePanel trace={message.trace} />}
          </div>
        ))}
        {state.loading && <TypingIndicator />}
      </div>

      <div style={{ borderTop: '1px solid #e5e7eb', backgroundColor: '#fff', padding: '12px' }}>
        {escalated && <EscalationBanner />}
        <form onSubmit={onSubmit} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={org ? `Ask about ${org}...` : 'Ask about AcmeCRM...'}
            style={{ flex: 1, borderRadius: '9999px', border: '1px solid #d1d5db', padding: '8px 14px', fontSize: '14px', outline: 'none', fontFamily: 'inherit' }}
          />
          <button
            type="submit"
            disabled={state.loading || !input.trim()}
            style={{ borderRadius: '9999px', backgroundColor: '#4f46e5', padding: '8px 16px', fontSize: '14px', fontWeight: 600, color: '#fff', border: 'none', cursor: 'pointer', opacity: state.loading || !input.trim() ? 0.5 : 1, fontFamily: 'inherit' }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
