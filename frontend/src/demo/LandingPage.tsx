import { useCallback, useEffect, useState } from 'react'
import App from '../App'
import ChatWidget from '../widget/ChatWidget'
import { fetchCompanies } from '../api/client'
import type { CompanyInfo } from '../api/client'

const DEFAULT_COMPANIES: CompanyInfo[] = [
  {
    id: 'acmecrm',
    display_name: 'AcmeCRM',
    description: 'cloud CRM for small teams',
    doc_count: 0,
  },
  {
    id: 'globex',
    display_name: 'Globex',
    description: 'e-commerce & marketplace platform',
    doc_count: 0,
  },
]

const HINTS: Record<string, string> = {
  acmecrm: 'Try: "What is the refund window?"',
  globex: 'Try: "What is your shipping policy?"',
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function ArchitectureDiagram() {
  const box =
    'rounded-lg border border-indigo-200 bg-white px-3 py-2 text-center text-xs font-medium text-gray-700 shadow-sm'
  const arrow = 'mx-auto h-3 w-0.5 bg-indigo-300'

  return (
    <div className="mx-auto mt-6 max-w-3xl rounded-2xl border border-gray-200 bg-gray-50 p-6 font-mono">
      <div className="grid grid-cols-1 items-center gap-2 sm:grid-cols-2">
        <div className={box}>User chat widget (React)</div>
        <div className={box}>FastAPI (POST /chat)</div>
      </div>
      <div className={arrow} />
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-center text-xs font-semibold text-indigo-800">
        LangGraph agentic flow
      </div>
      <div className="grid grid-cols-2 gap-2 py-3 sm:grid-cols-6">
        {['route', 'retrieve', 'grade', 'reformulate', 'generate', 'escalate'].map((node) => (
          <div
            key={node}
            className="rounded-md border border-indigo-100 bg-white px-1 py-1.5 text-center text-[10px] text-gray-600"
          >
            {node}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <div className={box}>ChromaDB vector store</div>
        <div className={box}>MCP tools (orders, tickets)</div>
        <div className={box}>Groq LLM (Llama 3.1)</div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const [companies, setCompanies] = useState<CompanyInfo[]>(DEFAULT_COMPANIES)
  const [companyId, setCompanyId] = useState('acmecrm')
  const [showAdmin, setShowAdmin] = useState(false)

  const refreshCompanies = useCallback(() => {
    fetchCompanies()
      .then((list) => {
        if (list.length > 0) setCompanies(list)
      })
      .catch(() => {
        // keep the hardcoded fallback if the backend is unreachable
      })
  }, [])

  useEffect(() => {
    refreshCompanies()
  }, [refreshCompanies])

  useEffect(() => {
    if (!showAdmin) refreshCompanies()
  }, [showAdmin, refreshCompanies])

  const active = companies.find((c) => c.id === companyId) ?? companies[0]

  if (showAdmin) {
    return (
      <>
        <App onBack={() => setShowAdmin(false)} />
        <ChatWidget apiUrl={API_URL} org={active?.display_name} company={active?.id} />
      </>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-100 text-gray-900">
      <div className="mx-auto max-w-4xl px-6 py-14 text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">
          Agentic RAG customer support
        </p>
        <h1 className="mt-3 text-5xl font-bold tracking-tight">
          Support<span className="text-indigo-600">IQ</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-gray-600">
          A customer support chatbot that answers from a company&apos;s own documents, grades
          whether its retrieval is good enough before answering, calls tools to check order status,
          and shows its reasoning right in the UI.
        </p>

        <div className="mx-auto mt-8 flex max-w-lg items-center gap-2 rounded-2xl border border-indigo-200 bg-white p-2 shadow-sm">
          <span className="pl-2 text-xs font-semibold uppercase text-gray-400">Demo Companies</span>
          <select
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            className="flex-1 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-800 outline-none focus:border-indigo-400"
          >
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.display_name} ({c.id})
              </option>
            ))}
          </select>
        </div>
        <p className="mt-3 text-sm text-gray-500">
          {active?.description && `${active.description} — `}
          {active?.id
            ? (HINTS[active.id] ?? `Ask anything about ${active.display_name}.`)
            : 'Select a company to start.'}
        </p>

        <ArchitectureDiagram />

        <div className="mx-auto mt-10 grid max-w-3xl gap-4 text-left sm:grid-cols-3">
          {[
            {
              title: 'Grades retrieval',
              body: 'Before answering, an LLM grader checks whether the retrieved chunks actually answer the question.',
            },
            {
              title: 'Reformulates & retries',
              body: 'Weak retrieval triggers one query rewrite and a second retrieval instead of guessing.',
            },
            {
              title: 'Escalates honestly',
              body: 'If still unanswered, the bot says so and hands off to a human — no hallucinated answers.',
            },
          ].map((f) => (
            <div key={f.title} className="rounded-2xl border border-gray-200 bg-white p-4">
              <h3 className="font-semibold text-indigo-700">{f.title}</h3>
              <p className="mt-1 text-sm text-gray-600">{f.body}</p>
            </div>
          ))}
        </div>

        <p className="mt-12 text-xs text-gray-400">
          Chat widget: <span className="font-mono">widget.js</span> embeddable bundle · LangChain +
          LangGraph + FastAPI · ChromaDB · MCP
        </p>
        <button
          onClick={() => setShowAdmin(true)}
          className="mt-3 text-xs font-medium text-indigo-500 hover:text-indigo-700"
        >
          Admin: upload documents →
        </button>
      </div>

      <ChatWidget
        key={companyId}
        apiUrl={API_URL}
        org={active?.display_name}
        company={companyId}
      />
    </div>
  )
}
