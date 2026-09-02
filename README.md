# SupportIQ

**SupportIQ** is an agentic RAG-powered customer support platform that gives businesses intelligent, document-grounded customer assistance through an embeddable chat widget, a multi-tenant knowledge base, tool calling via MCP, and human escalation workflows.

It combines retrieval-augmented generation with agentic reasoning — grading retrieval quality, reformulating queries when answers fall short, calling external tools, and escalating to a human when confidence is low.

<p align="center">
  <a href="https://support-iq-yk.vercel.app/"><strong>🔗 Live Demo</strong></a>
</p>

---

## 🚀 Live Demo

| App | URL |
|---|---|
| Frontend / Dashboard | [https://support-iq-yk.vercel.app/](https://support-iq-yk.vercel.app/) |
| Backend API | Hosted on Render |

> ⚠️ The backend runs on Render's free tier — the first request after a period of inactivity may take a few seconds to spin up.

---

## ✨ Features

### Agentic RAG Customer Support
- AI-powered customer conversations using Groq LLMs
- LangGraph-based agentic flow with retrieval grading and query reformulation
- Context-aware responses grounded in uploaded company documents
- Automatic escalation to human support when confidence is low
- Source citations displayed alongside every answer

### Multi-Tenant Knowledge Base (RAG)
- Per-company document storage via MongoDB GridFS
- File uploads: Markdown, TXT, RST, HTML, PDF
- Recursive text chunking (700 chars, 100 overlap)
- Jina AI embeddings (768-dim vectors, `jina-embeddings-v3`)
- ChromaDB per-company vector collections
- Startup vector rebuild for ephemeral deployment environments

### Tool Calling (MCP)
- Model Context Protocol integration via FastMCP
- Extensible tool server (order status lookup, ticket creation)
- LLM-driven tool selection and invocation
- Tool results fed back into generation context

### Embeddable Widget
- One-line installation via a `<script>` tag
- Floating chat bubble with expandable window
- IIFE bundle (React self-contained, `widget.js`)
- Configurable per-company deployment
- Dynamic CORS origin management with admin approval workflow

### Admin Dashboard
- Company creation and management
- Document upload and knowledge base management
- Widget embed code generation
- Origin approval request workflow
- User dashboard with company ownership

### Authentication & Authorization
- Clerk authentication (sign-in / sign-up)
- JWT verification on the backend
- Role-based access control (admin / owner / member)
- Per-route authorization for document and company operations

### Observability
- LangSmith tracing for LLM calls and graph execution
- Full trace visualization in the chat widget (collapsible trace panel)
- RAG retrieval sources displayed alongside responses

---

## 🏗️ Architecture Overview

SupportIQ consists of two major applications:

### 1. Backend Application (Python)

**Location:** `backend/`

**Purpose:**
- FastAPI REST API
- LangGraph agentic RAG flow
- ChromaDB vector storage
- MongoDB document persistence
- MCP tool server
- Clerk JWT authentication
- Dynamic CORS origin management

**Technology:**
- Python 3.11
- FastAPI + Uvicorn
- LangChain + LangGraph
- ChromaDB
- MongoDB (pymongo) + GridFS
- Jina AI Embeddings
- Groq LLM
- FastMCP (Model Context Protocol)
- Clerk Backend API
- LangSmith

### 2. Frontend Application (React)

**Location:** `frontend/`

**Purpose:**
- Chat widget (embeddable IIFE bundle)
- Admin dashboard
- User dashboard
- Landing / demo page
- Widget embed script generation

**Technology:**
- React 19 + TypeScript
- Vite 8
- Tailwind CSS 4
- React Router 7
- Clerk React SDK
- Axios

---

## 🔭 High-Level Architecture

```
Customer Website
        |
        | <script src="widget.js">
        v
Embed Script (widget.js IIFE bundle)
        |
        | Creates floating bubble + chat window
        v
Frontend (React SPA)
        |
        +---> Authenticated Dashboard         +---> Admin Panel
        |
        v
Backend (FastAPI)
        |
        +---> Clerk Auth (JWT verification)
        |
        +---> MongoDB (companies, documents, origins)
        |
        +---> ChromaDB (per-company vector collections)
        |
        +---> LangGraph Agentic Flow
        |         |
        |         +---> Route Node (intent classification)
        |         +---> Retrieve Node (similarity search)
        |         +---> Grade Node (relevance check)
        |         +---> Reformulate Node (query rewriting)
        |         +---> Generate Node (grounded answer)
        |         +---> Tool Node (MCP tool calls)
        |         +---> Escalate Node (human handoff)
        |
        +---> Groq LLM
        +---> Jina Embeddings
        +---> MCP Tools (order status, tickets)
```

### Agentic AI Conversation Flow

```
Customer Message
       |
       v
  Route Node
       |
       +---> "faq" ---------> Retrieve Node (ChromaDB top-5)
       |                              |
       |                              v
       |                         Grade Node
       |                              |
       |                     +--------+--------+
       |                     |                 |
       |                "relevant"      "insufficient"
       |                     |                 |
       |                     v                 v
       |              Generate Node     Reformulate Node
       |                     |                 |
       |                     v                 v
       |              AI Response        Retry Retrieve
       |
       +---> "tool_use" ---> Tool Node (MCP) ---> Generate Node
       |
       +---> "wants_human" -> Escalate Node
```

### Chat Request Lifecycle

```
Customer Message
        ↓
Chat Widget
        ↓
POST /chat
        ↓
FastAPI Router
        ↓
LangGraph Agentic Flow (run_rag)
        ↓
Route → Retrieve → Grade → (Reformulate → Retrieve) → Generate / Tool / Escalate
        ↓
ChatResponse { answer, sources, trace }
        ↓
Widget Display (with collapsible trace panel)
```

---

## 🏢 Session & Origin Management

**Company-based multi-tenancy:**
- Each company has an isolated document compartment, vector collection, and chat context
- Company owners can upload/delete documents
- Admins manage all companies and origin approvals
- `DEFAULT_COMPANY_ID` provides a fallback when no company is specified

**Origin access control:**
- Users submit origin approval requests for their websites
- Admins approve or reject requests via the admin panel
- Approved origins are dynamically added to the CORS allowlist
- No server restart needed — origin changes take effect on the next request via `DynamicCorsMiddleware`

---

## 🧩 Embedding the Widget

```html
<script
  src="https://your-domain.com/widget.js"
  data-api-url="https://your-backend.com"
  data-company="YOUR_COMPANY_ID"
  data-org="Your Organization Name">
</script>
```

The embed script automatically:
- Creates a floating chat button in the bottom-right corner
- Opens a chat window on click
- Connects to the configured backend API
- Displays AI responses with source citations
- Shows collapsible RAG trace panels
- Supports escalation to human support

---

## 🛠️ Local Development

### Install Dependencies

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Start Development Environment

**Backend (Terminal 1):**
```bash
cd backend
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### Ingest Company Documents
```bash
cd backend
python scripts/ingest.py --company acmecrm
```

### Test Similarity Search
```bash
cd backend
python scripts/search.py "what is your refund policy?" --company acmecrm
```

### Test Widget Embed
Open `test.html` in a browser (with the backend running) to see the embedded widget.

---

## 📦 Build

**Frontend (including widget):**
```bash
cd frontend
npm run build
# Builds SPA + widget.js IIFE bundle
```

**Widget only:**
```bash
cd frontend
npm run build:widget
# Outputs dist-widget/widget.js
```

**Lint:**
```bash
cd frontend
npm run lint
```

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq LLM API key |
| `CLERK_SECRET_KEY` | Yes | Clerk backend secret key |
| `CLERK_AUTHORIZED_PARTIES` | Yes | Comma-separated allowed auth origins |
| `JINA_API_KEY` | Yes | Jina embeddings API key |
| `MONGODB_URI` | Optional | MongoDB Atlas connection string (falls back to disk) |
| `MONGODB_DB_NAME` | Optional | Database name (default: `supportiq`) |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing key |
| `LANGCHAIN_TRACING_V2` | Optional | Set to `"true"` to enable tracing |
| `LANGCHAIN_ENDPOINT` | Optional | LangSmith API endpoint |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name (default: `supportiq`) |
| `ALLOWED_ORIGINS` | Optional | Fallback CORS origin list |

### Frontend (`frontend/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | Yes | Clerk frontend publishable key |
| `VITE_API_URL` | Optional | Backend URL (default: `http://localhost:8000`) |

---

## 🧰 Tech Stack

**Backend**
- Python 3.11
- FastAPI + Uvicorn
- LangChain + LangGraph
- ChromaDB (vector store)
- MongoDB + GridFS (document storage)
- Jina AI Embeddings (768-dim)
- Groq LLM (openai/gpt-oss-20b)
- FastMCP (Model Context Protocol)
- Clerk Backend API (auth)
- LangSmith (observability)

**Frontend**
- React 19
- TypeScript
- Vite 8
- Tailwind CSS 4
- React Router 7
- Clerk React SDK
- Axios
- Oxlint

**Deployment**
- Backend: Render
- Frontend: Vercel
- Database: MongoDB Atlas (optional, falls back to local JSON/disk)
- Vector Store: ChromaDB (local file / ephemeral on Render)

---

## 🌟 Project Highlights
- Agentic RAG with retrieval grading and query reformulation
- Multi-tenant per-company knowledge base isolation
- MCP tool calling for external system integration
- Embeddable widget with one-line installation
- Dynamic CORS origin management with admin approval
- Full RAG trace visualization in the chat UI
- Human escalation when AI confidence is low
- Clerk-based JWT auth with role-based access control
- Startup vector rebuild for ephemeral deployment environments
- LangSmith observability for LLM call tracing

---

## 🗺️ Future Improvements
- Multi-language AI support
- Advanced analytics dashboard
- Conversation sentiment analysis
- Workflow builder for custom escalation rules
- CRM integrations
- Slack integration
- Email automation
- Custom AI agent configuration per company
- Subscription-based premium features
- Real-time human operator dashboard

---

## 🎯 Project Goal

SupportIQ aims to provide businesses with a complete AI-powered customer support solution that combines:

- **Agentic RAG** — AI that reasons about its own retrieval quality
- **Document Grounding** — Responses sourced from the company knowledge base
- **Tool Calling** — Integration with external systems via MCP
- **Human Escalation** — Seamless handoff when AI confidence is low
- **Multi-Tenancy** — Isolated per-company knowledge and configuration
- **Easy Integration** — Embeddable widget via a single script tag

...into a single, scalable SaaS platform.
