# SupportIQ — Agentic RAG Customer Support System
## Full Build Documentation (for AI-assisted / vibe-coding development)

> **How to use this doc:** Follow phases in order. Each phase has a goal, exact tasks, file/folder targets, and a "Definition of Done" checklist. Do NOT skip a phase's Definition of Done before moving to the next — later phases depend on earlier ones working correctly. If using an AI coding tool (Claude Code, Cursor, etc.), paste one phase at a time as the task and let it complete + verify the Definition of Done before moving on.

---

## 0. Project Overview

**What we're building:** A customer support chatbot that answers questions using a company's own documents (RAG), reasons about whether its retrieved info is good enough before answering (agentic grading via LangGraph), can call tools to check things like order status (MCP), and shows its reasoning process in the UI.

**Tech stack:**
| Layer | Tech |
|---|---|
| Backend framework | FastAPI (Python) |
| LLM orchestration | LangChain + LangGraph |
| Tool protocol | MCP (Model Context Protocol) |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) — free, local |
| Vector store | ChromaDB — free, local, file-based |
| LLM | Groq (Llama 3.1/3.3) or Gemini free tier |
| Observability | LangSmith |
| Frontend | React + Vite + TypeScript |
| Styling | Tailwind CSS |
| Deployment | Backend → Render/Railway free tier; Frontend → Vercel |

**Repo structure (monorepo):**
```
supportiq/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── ingestion/
│   │   │   ├── loader.py
│   │   │   ├── chunker.py
│   │   │   └── embedder.py
│   │   ├── rag/
│   │   │   ├── vectorstore.py
│   │   │   └── retriever.py
│   │   ├── graph/
│   │   │   ├── state.py
│   │   │   ├── nodes.py
│   │   │   └── build_graph.py
│   │   ├── mcp_tools/
│   │   │   ├── server.py
│   │   │   └── tools.py
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   └── upload.py
│   │   └── models/
│   │       └── schemas.py
│   ├── data/
│   │   ├── raw_docs/
│   │   └── chroma_db/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── widget/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   ├── EscalationBanner.tsx
│   │   │   ├── TracePanel.tsx
│   │   │   └── ChatWidget.tsx
│   │   ├── admin/
│   │   │   └── UploadPanel.tsx
│   │   ├── demo/
│   │   │   └── LandingPage.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── embed-entry.tsx
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── vite.widget.config.ts
│   └── package.json
└── README.md
```

---

## Phase 0 — Environment Setup

**Goal:** Empty-but-runnable skeleton for both backend and frontend.

**Tasks:**
1. Create the folder structure above (empty files are fine for now).
2. Backend: create a Python virtual environment, `pip install fastapi uvicorn langchain langchain-community langgraph langchain-groq sentence-transformers chromadb python-multipart python-dotenv pypdf`
3. Create `backend/.env`:
   ```
   GROQ_API_KEY=your_key_here
   LANGCHAIN_API_KEY=your_langsmith_key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=supportiq
   ```
4. Frontend: `npm create vite@latest frontend -- --template react-ts`, then `npm install` and `npm install -D tailwindcss postcss autoprefixer axios`, init Tailwind.
5. Confirm `uvicorn app.main:app --reload` runs a "hello world" FastAPI app on `localhost:8000`.
6. Confirm `npm run dev` runs the Vite React app on `localhost:5173`.

**Definition of Done:**
- [ ] `localhost:8000/docs` shows FastAPI's Swagger UI
- [ ] `localhost:5173` shows the default Vite React page
- [ ] `.env` loads correctly (`print(os.getenv("GROQ_API_KEY"))` returns your key, not `None`)

---

## Phase 1 — Ingestion Pipeline (backend, script-level, no API yet)

**Goal:** A standalone script that takes docs and produces a queryable vector store.

**Tasks:**
1. Drop 5–10 sample docs into `backend/data/raw_docs/` (markdown or PDF — e.g. a fake SaaS product's FAQ, refund policy, setup guide).
2. `app/ingestion/loader.py`: function `load_documents(path: str) -> list[Document]` using LangChain's `DirectoryLoader` / `PyPDFLoader` / `TextLoader` depending on file type.
3. `app/ingestion/chunker.py`: function `chunk_documents(docs) -> list[Document]` using `RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)`.
4. `app/ingestion/embedder.py`: function `get_embedding_model()` returning a `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` instance.
5. `app/rag/vectorstore.py`:
   - `build_vectorstore(chunks, embedding_model)` — creates and persists a Chroma DB at `backend/data/chroma_db`
   - `load_vectorstore(embedding_model)` — loads the existing persisted Chroma DB
6. Write a one-off script `backend/scripts/ingest.py` that: loads docs → chunks → embeds → builds vectorstore → prints "Ingested N chunks from M docs".
7. Run it. Then write a second scratch script that loads the vectorstore and does `.similarity_search("sample question", k=3)` — manually confirm the returned chunks are actually relevant.

**Definition of Done:**
- [ ] `python scripts/ingest.py` runs without error and populates `data/chroma_db/`
- [ ] A manual similarity search for a question you know the answer to (from your sample docs) returns the correct chunk in the top 3 results

---

## Phase 2 — Basic RAG API

**Goal:** `/chat` and `/upload` endpoints working, testable via Swagger UI or curl — no frontend yet.

**Tasks:**
1. `app/models/schemas.py`: Pydantic models —
   ```python
   class ChatRequest(BaseModel):
       message: str
       conversation_id: str

   class ChatResponse(BaseModel):
       answer: str
       sources: list[str]
   ```
2. `app/rag/retriever.py`: function `get_answer(query: str) -> ChatResponse` that: retrieves top-k chunks from Chroma → builds a prompt (system prompt: "Answer only using the provided context. If the context doesn't contain the answer, say you don't know.") → calls the LLM (Groq via `langchain-groq`'s `ChatGroq`) → returns answer + list of source filenames.
3. `app/routes/chat.py`: `POST /chat` endpoint wired to `get_answer`.
4. `app/routes/upload.py`: `POST /upload` endpoint — accepts a file via `UploadFile`, saves to `data/raw_docs/`, runs it through the Phase 1 pipeline, appends to the existing vectorstore (use Chroma's `.add_documents`, don't rebuild from scratch).
5. `app/main.py`: wire both routers into the FastAPI app, enable CORS for `localhost:5173`.

**Definition of Done:**
- [ ] `POST /chat` with `{"message": "<a question your docs answer>", "conversation_id": "test"}` returns a correct, grounded answer with real source filenames
- [ ] `POST /chat` with an off-topic question returns an "I don't know" style answer, not a hallucinated one
- [ ] `POST /upload` with a new doc successfully adds it — a follow-up `/chat` question about that doc's content works

---

## Phase 3 — LangGraph Agentic Flow

**Goal:** Replace the simple retrieve→generate call with a graph that routes, grades retrieval quality, and can escalate.

**Tasks:**
1. `app/graph/state.py`: define the graph state (a `TypedDict`):
   ```python
   class GraphState(TypedDict):
       question: str
       chunks: list[str]
       sources: list[str]
       grade: str          # "relevant" | "insufficient"
       reformulated: str | None
       escalated: bool
       answer: str
   ```
2. `app/graph/nodes.py` — implement each node as a function `(state) -> state`:
   - `route_node`: classify intent (simple keyword/LLM classification — "faq" vs "wants_human")
   - `retrieve_node`: runs similarity search, fills `chunks` + `sources`
   - `grade_node`: asks the LLM "Do these chunks answer this question? yes/no" → sets `grade`
   - `reformulate_node`: if grade is "insufficient" and it's the first pass, rewrite the query and loop back to `retrieve_node` (cap at 1 retry to avoid infinite loops)
   - `generate_node`: produces the final grounded answer from `chunks`
   - `escalate_node`: if grade is still "insufficient" after retry, or intent was "wants_human", set `escalated = True` and set a canned "connecting you to a human" answer
3. `app/graph/build_graph.py`: wire nodes into a `StateGraph` with conditional edges:
   - `route_node` → `retrieve_node` (always) or straight to `escalate_node` (if "wants_human")
   - `retrieve_node` → `grade_node`
   - `grade_node` → `generate_node` (if relevant) or `reformulate_node` (if insufficient, first try) or `escalate_node` (if insufficient, second try)
   - `reformulate_node` → `retrieve_node`
   - `generate_node` → `END`
   - `escalate_node` → `END`
4. Update `app/rag/retriever.py` (or replace with `app/graph/run.py`) so `/chat` invokes the compiled graph instead of the plain chain, and returns the full trace:
   ```python
   class ChatResponse(BaseModel):
       answer: str
       sources: list[str]
       trace: dict  # {retrieved_chunks, grading, reformulated_query, escalated}
   ```

**Definition of Done:**
- [ ] A question your docs answer well → single retrieve → grade "relevant" → direct answer, `escalated: false`
- [ ] A vaguely-worded question that needs reformulation → you can see `reformulated_query` populated in the trace and a correct final answer
- [ ] A question totally outside your docs → `escalated: true`, canned handoff message
- [ ] LangSmith dashboard shows traces for each of the above runs

---

## Phase 4 — MCP Tool Integration

**Goal:** Agent can call tools (mocked) mid-conversation.

**Tasks:**
1. `app/mcp_tools/tools.py`: define 2 mock tool functions:
   - `check_order_status(order_id: str) -> dict` — returns fake hardcoded data based on `order_id`
   - `create_ticket(issue: str) -> dict` — returns a fake ticket ID
2. `app/mcp_tools/server.py`: expose these as MCP tools using the `mcp` Python SDK's `FastMCP` server pattern (register tool functions with decorators, run as a local MCP server process).
3. In `app/graph/nodes.py`, add a `tool_node` (or extend `route_node`) so if the LLM's classification detects an order/ticket-related intent, the graph calls the MCP tool client, gets the result, and feeds it into `generate_node` as extra context.
4. Update `route_node`'s classification to include a `"tool_use"` branch alongside `"faq"` and `"wants_human"`.

**Definition of Done:**
- [ ] Asking "what's the status of order #1234" triggers the tool call and returns the mock data in a natural-language answer
- [ ] Trace object shows which tool was called and with what arguments

---

## Phase 5 — Frontend: Chat Widget

**Goal:** Working chat UI hitting the real backend, including the reasoning trace panel.

**Tasks:**
1. `src/api/client.ts`: `sendMessage(message, conversationId)` — POSTs to `http://localhost:8000/chat`, returns typed `ChatResponse`.
2. `src/widget/MessageBubble.tsx`: renders a message; if it's a bot message, show an expandable "Sources" line under it.
3. `src/widget/TracePanel.tsx`: collapsible panel rendering `trace` — show retrieved chunks (truncated), grading result, whether reformulation happened, escalation status. Default collapsed, click to expand.
4. `src/widget/TypingIndicator.tsx`: animated dots shown while awaiting response.
5. `src/widget/EscalationBanner.tsx`: shown above the input when `trace.escalated === true`.
6. `src/widget/ChatWindow.tsx`: message list (maps over messages, renders `MessageBubble` + `TracePanel` for bot messages) + text input + send button. State via `useReducer`: `{messages: [], loading: false}`.
7. `src/widget/ChatWidget.tsx`: top-level wrapper — floating button that opens/closes `ChatWindow` (fixed position, bottom-right).

**Definition of Done:**
- [ ] Typing a question and hitting send shows a typing indicator, then a real answer from the backend
- [ ] Clicking "Sources" under a bot message expands to show source filenames
- [ ] Clicking the trace panel expands to show the routing/grading steps for that specific answer
- [ ] Asking an out-of-scope question shows the `EscalationBanner`

---

## Phase 6 — Embeddable Widget Bundle

**Goal:** The same widget can be dropped onto any external HTML page via a `<script>` tag.

**Tasks:**
1. `src/embed-entry.tsx`: entry point that finds a container div (created by a loader script) and mounts `<ChatWidget />` into it via `ReactDOM.createRoot`.
2. `vite.widget.config.ts`: separate Vite config building in **library mode**, entry = `embed-entry.tsx`, output = single IIFE bundle `widget.js` (bundle React itself into the output, no external deps assumed).
3. Write a tiny loader script (`public/loader.js` or inline in the bundle's own init code) that: on load, creates a floating button + container div, injects the widget bundle, mounts it.
4. Add an npm script: `"build:widget": "vite build --config vite.widget.config.ts"`.
5. Test: build it, then create a throwaway static `test.html` file elsewhere with just `<script src="/path/to/widget.js" data-org="demo"></script>` and open it directly in a browser — confirm the widget mounts and talks to your backend (watch for CORS issues, adjust FastAPI CORS config as needed).

**Definition of Done:**
- [ ] `npm run build:widget` produces a single `widget.js` file
- [ ] Dropping that script tag into a completely separate static HTML file successfully renders and runs the chat widget

---

## Phase 7 — Admin/Upload Panel

**Goal:** Visible proof the ingestion side of RAG works, not just chat.

**Tasks:**
1. `src/admin/UploadPanel.tsx`: file input + upload button, POSTs to `/upload`, shows a success message with chunk count returned from the backend.
2. Update `app/routes/upload.py` to return `{"filename": ..., "chunks_added": N}` so the frontend has something to display.

**Definition of Done:**
- [ ] Uploading a new doc through the UI shows a confirmation with the chunk count
- [ ] A follow-up chat question about that doc's content returns a correct answer with the new doc as a source

---

## Phase 8 — Landing/Demo Page

**Goal:** One URL that shows the whole project working, no setup required for a visitor.

**Tasks:**
1. `src/demo/LandingPage.tsx`: short pitch text, an architecture diagram image (draw on Excalidraw, export PNG, drop in `public/`), and the `<ChatWidget />` embedded live, pre-pointed at a backend that's pre-loaded with a fake company's docs.
2. Pre-seed the deployed backend's vectorstore with your sample docs at deploy time (run `scripts/ingest.py` once against production data, or run it as a startup step).
3. Make this page `main.tsx`'s default route.

**Definition of Done:**
- [ ] Opening the deployed frontend URL cold, with no prior setup, lets you immediately type a question and get a real grounded answer

---

## Phase 9 — Deployment

**Tasks:**
1. Backend → Render or Railway:
   - Push `backend/` as its own deployable service (or configure the monorepo's root/start command)
   - Set environment variables (`GROQ_API_KEY`, `LANGCHAIN_API_KEY`, etc.) in the platform's dashboard
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Note the deployed backend URL
2. Frontend → Vercel:
   - Set the backend URL as an environment variable (`VITE_API_URL`) and use it in `src/api/client.ts` instead of hardcoding `localhost:8000`
   - Deploy `frontend/`
3. Update CORS in `app/main.py` to allow the deployed frontend's domain.
4. Re-test the full flow against the deployed URLs (not localhost).

**Definition of Done:**
- [ ] Live frontend URL works end-to-end against the live backend
- [ ] No CORS errors, no hardcoded `localhost` references left in frontend code

---

## Phase 10 — README + Resume Polish

**Tasks:**
1. Write `README.md` with, in this order: one-line pitch → live demo link → architecture diagram → "why LangGraph over a plain RAG chain" section (2–3 sentences on the grading/reformulation/escalation logic) → LangSmith trace screenshot → local setup instructions → future improvements list.
2. Resume bullet:
   > Built an agentic RAG-based customer support system using LangChain, LangGraph, FastAPI, and MCP; implemented query grading and re-retrieval to reduce hallucinated responses, with tool-calling for live order/ticket actions.
3. Add the live demo link to your portfolio site and resume header, not just the GitHub repo link.

**Definition of Done:**
- [ ] README is readable top-to-bottom by someone who has never seen the project
- [ ] Live link, GitHub link, and resume bullet are all consistent with each other

---

## Notes for AI-assisted ("vibe coding") execution
- Work through phases strictly in order — each Definition of Done gates the next phase.
- After each phase, actually run and manually test it before proceeding — don't trust "should work."
- If a phase's tasks feel too large for one sitting, split by numbered task, not by file — finish task 1 for all its files before starting task 2.
- Keep `.env` files out of git (`.gitignore` from Phase 0 onward).
- If the LLM/embedding provider changes (e.g. swapping Groq for Gemini), only `app/rag/retriever.py` / `app/graph/nodes.py`'s LLM-calling lines should need edits — keep provider-specific code isolated there.
