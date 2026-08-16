import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import ChatWidget from './widget/ChatWidget'
import styles from './index.css?inline'

export interface EmbedOptions {
  /** Backend base URL, e.g. http://localhost:8000 */
  apiUrl?: string
  /** Organization / product name shown in the widget header */
  org?: string
  /** Company id whose knowledge base the widget answers from, e.g. acmecrm */
  company?: string
}

const STYLE_ID = 'supportiq-widget-styles'
const CONTAINER_ID = 'supportiq-widget-root'

let root: Root | null = null
let currentOptions: EmbedOptions = {}

function injectStyles(): void {
  if (document.getElementById(STYLE_ID)) return
  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = styles
  document.head.appendChild(style)
}

function readScriptOptions(): EmbedOptions {
  const script = document.currentScript as HTMLScriptElement | null
  if (!script?.dataset) return {}
  const options: EmbedOptions = {}
  if (script.dataset.apiUrl) options.apiUrl = script.dataset.apiUrl
  if (script.dataset.org) options.org = script.dataset.org
  if (script.dataset.company) options.company = script.dataset.company
  return options
}

function ensureContainer(): HTMLDivElement {
  let el = document.getElementById(CONTAINER_ID) as HTMLDivElement | null
  if (!el) {
    el = document.createElement('div')
    el.id = CONTAINER_ID
    document.body.appendChild(el)
  }
  return el
}

/** Mount (or re-render) the chat widget. Safe to call more than once. */
export function init(options: EmbedOptions = {}): void {
  currentOptions = { ...readScriptOptions(), ...currentOptions, ...options }
  injectStyles()
  if (!root) {
    root = createRoot(ensureContainer())
  }
  root.render(<ChatWidget apiUrl={currentOptions.apiUrl} org={currentOptions.org} company={currentOptions.company} />)
}

declare global {
  interface Window {
    SupportIQ?: { init: typeof init }
  }
}

function bootstrap(): void {
  window.SupportIQ = { init }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init())
  } else {
    init()
  }
}

bootstrap()
