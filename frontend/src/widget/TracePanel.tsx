import { useState } from 'react'
import type { Trace } from '../api/client'

export default function TracePanel({ trace }: { trace: Trace }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-1.5 text-xs">
      <button
        onClick={() => setOpen((v) => !v)}
        className="font-medium text-gray-400 hover:text-gray-600"
      >
        {open ? '▾' : '▸'} Trace
      </button>
      {open && (
        <div className="mt-1 space-y-1.5 rounded-lg border border-gray-200 bg-gray-50 p-2.5 font-mono text-[11px] text-gray-600">
          <div>
            <span className="font-semibold">intent:</span> {trace.intent ?? '—'}
          </div>
          <div>
            <span className="font-semibold">grading:</span> {trace.grading ?? '—'}
          </div>
          <div>
            <span className="font-semibold">reformulated:</span>{' '}
            {trace.reformulated_query ? `"${trace.reformulated_query}"` : 'no'}
          </div>
          <div>
            <span className="font-semibold">escalated:</span>{' '}
            {String(trace.escalated ?? false)}
          </div>
          {trace.tool_calls.length > 0 && (
            <div>
              <span className="font-semibold">tool_calls:</span>{' '}
              {trace.tool_calls
                .map((tc) => `${tc.name}(${JSON.stringify(tc.arguments)})`)
                .join(', ')}
            </div>
          )}
          <div className="border-t border-gray-200 pt-1.5">
            <div className="mb-0.5 font-semibold">
              retrieved chunks ({trace.retrieved_chunks.length})
            </div>
            {trace.retrieved_chunks.map((chunk, i) => (
              <div key={i} className="truncate text-gray-500">
                [{i + 1}] {chunk.replace(/\s+/g, ' ').slice(0, 120)}…
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
