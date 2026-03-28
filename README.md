# Debuggable AI Assistant

Production-ready project that demonstrates a full-stack AI troubleshooting workflow:

- FastAPI backend with structured logging, authentication, caching, SSE streaming, and contract-safe endpoints
- LangChain-based RAG pipeline with document ingestion and vector retrieval (Chroma)
- React frontend chat app with loading states, error handling, and a live debug panel
- Realistic bug scenario: legacy API response mismatch vs frontend expectations, then fixed with response normalization and contract-safe endpoint usage

## Architecture

```text
React UI
  -> FastAPI /api/chat or /api/chat/stream
    -> RAG retrieval (LangChain + Chroma)
    -> LLM generation (OpenAI if key present, deterministic fallback if no key)
    -> JSON logs + trace IDs
```

### Components

- `frontend/`: React app (Vite) with chat panel and debug panel
- `backend/`: FastAPI app, RAG services, logging, auth, tests
- `backend/data/docs/`: initial knowledge base files for ingestion

## Project Structure

```text
.
├── backend
│   ├── app
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── main.py
│   │   ├── routes
│   │   │   ├── chat.py
│   │   │   ├── debug.py
│   │   │   └── documents.py
│   │   ├── schemas.py
│   │   └── services
│   │       ├── llm.py
│   │       ├── logger.py
│   │       └── rag.py
│   ├── data/docs/debugging_playbook.txt
│   ├── requirements.txt
│   └── tests/test_api.py
├── frontend
│   ├── package.json
│   ├── src
│   │   ├── App.jsx
│   │   ├── components/ChatWindow.jsx
│   │   ├── components/DebugPanel.jsx
│   │   ├── lib/api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   └── vite.config.js
├── .env.example
└── README.md
```

## FastAPI Endpoints

### Health
- `GET /health`

### Chat and Streaming
- `POST /api/chat`
- `POST /api/chat/stream` (SSE)
- `POST /api/chat/legacy` (intentional legacy bug shape)

### RAG and Documents
- `GET /api/documents`
- `POST /api/documents/ingest`

### Debugging
- `GET /api/debug/logs`

### Auth
All `/api/*` endpoints require `x-api-key` header.

## Bug Scenario and Fix

### Introduced Bug
A legacy endpoint returns incompatible keys:

- Legacy: `response`, `source_items`, `request_id`
- Stable contract: `answer`, `sources`, `trace_id`

This reflects a real migration bug where backend and frontend versions drift.

### Detection
- Frontend debug panel shows raw payload
- Backend JSON logs show `legacy_response_format_detected`
- Integration tests lock expected fields for both new and legacy shapes

### Fix
- Primary UI path uses `/api/chat` stable contract
- Frontend `normalizeChatResponse` maps either shape to one UI contract
- Debug toggle allows reproducing the legacy issue safely for demos

## Setup

## 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

## 2) Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 VITE_API_KEY=debug-assistant-key npm run dev
```

## Example Requests and Responses

### Ingest Document

```bash
curl -X POST http://localhost:8000/api/documents/ingest \
  -H 'content-type: application/json' \
  -H 'x-api-key: debug-assistant-key' \
  -d '{"file_name":"incident.txt","content":"Timeout happened because upstream took 30s"}'
```

Response:

```json
{
  "file_name": "incident.txt",
  "chunks_added": 1
}
```

### Chat (Stable)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -H 'x-api-key: debug-assistant-key' \
  -d '{"message":"How should I trace timeout issues?","top_k":3}'
```

Response:

```json
{
  "answer": "Based on retrieved context: ...",
  "sources": [
    {"source": "backend/data/docs/debugging_playbook.txt", "snippet": "When debugging API flows..."}
  ],
  "trace_id": "f1a6...",
  "debug": {"context_count": 3, "cache_hit": false}
}
```

### Chat (Legacy Bug)

```bash
curl -X POST http://localhost:8000/api/chat/legacy \
  -H 'content-type: application/json' \
  -H 'x-api-key: debug-assistant-key' \
  -d '{"message":"legacy shape","top_k":1}'
```

Response:

```json
{
  "response": "Based on retrieved context: ...",
  "source_items": [
    {"source": "backend/data/docs/debugging_playbook.txt", "snippet": "When debugging API flows..."}
  ],
  "request_id": "a9d2...",
  "meta": {"context_count": 1, "cache_hit": true}
}
```

## Debugging Flow Demonstration

1. Enable Legacy Bug Mode in UI.
2. Send a message and inspect debug panel raw payload.
3. Observe schema mismatch keys and backend logs.
4. Disable Legacy Bug Mode and retry.
5. Verify normalized payload and trace ID continuity.

## Project Value

This project demonstrates:

- API contract management under evolving backend versions
- Structured observability (trace IDs + logs)
- Practical RAG integration and context retrieval tuning
- Resilient frontend integration with fallbacks and streaming
- Real incident simulation with reproducible bug mode and clear fix path
