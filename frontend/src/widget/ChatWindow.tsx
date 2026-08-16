import { useEffect, useReducer, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { sendMessage } from '../api/client'
import { uid } from './id'
import type { ChatMessage } from './types'
import EscalationBanner from './EscalationBanner'
import MessageBubble from './MessageBubble'
import TracePanel from './TracePanel'
import TypingIndicator from './TypingIndicator'

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
    <div className="flex h-[min(560px,calc(100dvh-100px))] w-[min(380px,calc(100vw-24px))] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 shadow-xl">
      <div className="flex items-center justify-between bg-indigo-600 px-4 py-3 text-white">
        <div>
          <div className="text-sm font-semibold">SupportIQ</div>
          <div className="text-[11px] text-indigo-200">
            {org ? `AI support for ${org}` : 'AI support assistant'}
          </div>
        </div>
      </div>

      <div ref={listRef} className="flex-1 space-y-2.5 overflow-y-auto p-3">
        {state.messages.map((message) => (
          <div key={message.id}>
            <MessageBubble message={message} />
            {message.role === 'bot' && message.trace && <TracePanel trace={message.trace} />}
          </div>
        ))}
        {state.loading && <TypingIndicator />}
      </div>

      <div className="border-t border-gray-200 bg-white p-3">
        {escalated && <EscalationBanner />}
        <form onSubmit={onSubmit} className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={org ? `Ask about ${org}...` : 'Ask about AcmeCRM...'}
            className="flex-1 rounded-full border border-gray-300 px-3.5 py-2 text-sm outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={state.loading || !input.trim()}
            className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
