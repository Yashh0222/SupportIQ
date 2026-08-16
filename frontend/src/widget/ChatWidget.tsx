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
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 2147483647, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px' }}>
      {open && (
        <ChatWindow conversationId={conversationId} apiUrl={apiUrl} org={org} company={company} />
      )}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Toggle chat"
        style={{ display: 'flex', height: '56px', width: '56px', alignItems: 'center', justifyContent: 'center', borderRadius: '50%', backgroundColor: '#4f46e5', color: '#fff', boxShadow: '0 4px 12px rgba(0,0,0,0.25)', border: 'none', cursor: 'pointer', transition: 'background-color 0.2s' }}
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
