import { useRef, useState } from 'react'
import ChatWindow from './ChatWindow'
import { uid } from './id'

export interface ChatWidgetProps {
  apiUrl?: string
  org?: string
  company?: string
}

export default function ChatWidget({ apiUrl, org, company }: ChatWidgetProps = {}) {
  const [open, setOpen] = useState(false)
  const conversationId = useRef(uid()).current

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      {open && (
        <ChatWindow conversationId={conversationId} apiUrl={apiUrl} org={org} company={company} />
      )}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Toggle chat"
        className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg transition hover:bg-indigo-700"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {open ? (
            <path d="M18 6 6 18M6 6l12 12" />
          ) : (
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          )}
        </svg>
      </button>
    </div>
  )
}
