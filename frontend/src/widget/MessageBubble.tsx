import { useState } from 'react'
import type { ChatMessage } from './types'

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  const [showSources, setShowSources] = useState(false)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[82%] rounded-2xl px-3.5 py-2 text-sm shadow-sm ${
          isUser
            ? 'rounded-br-sm bg-indigo-600 text-white'
            : 'rounded-bl-sm border border-gray-200 bg-white text-gray-800'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <button
            onClick={() => setShowSources((v) => !v)}
            className="mt-2 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            Sources ({message.sources.length}) {showSources ? '▴' : '▾'}
          </button>
        )}
        {!isUser && showSources && message.sources && (
          <ul className="mt-1 space-y-0.5">
            {message.sources.map((source) => (
              <li key={source} className="break-all text-xs text-gray-500">
                • {source}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
