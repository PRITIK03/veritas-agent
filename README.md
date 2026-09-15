# Veritas Agent

A grounded RAG + web-search pipeline that verifies every answer against its sources before returning it. Built with LangGraph, Gemini, FAISS, Tavily, FastAPI.

---

## What it does

Every query runs through a four-node LangGraph pipeline:

```
Query → Router → [RAG | Web Search] → Grounding check → Response
```

1. **Router** — Gemini decides whether the query is covered by the internal knowledge base or needs a live web search.
2. **RAG specialist** — retrieves the top-k passages from a local FAISS index and generates an answer grounded in those passages.
3. **Web-search specialist** — searches via Tavily and generates an answer grounded in the returned pages.
4. **Grounding node** — Gemini fact-checks the answer against the retrieved context and stamps it `GROUNDED` or `NOT_GROUNDED` with a reason.

Every result is logged to Postgres with route, answer, sources, grounding verdict, latency, token count, and estimated cost.

---

## Project structure

```
veritas-agent/
├── app/
│   ├── main.py            # FastAPI — POST /query, GET /health, GET /analytics
│   ├── config.py          # Settings loaded from .env
│   ├── db.py              # Postgres logging + analytics queries
│   ├── graph/
│   │   ├── state.py       # GraphState TypedDict
│   │   ├── router.py      # Routing node
│   │   ├── specialists.py # RAG + web-search answer nodes
│   │   ├── grounding.py   # Fact-checking node
│   │   └── pipeline.py    # LangGraph wiring
│   ├── rag/
│   │   ├── ingest.py      # Chunk, embed, build FAISS index
│   │   └── retriever.py   # Vector search
│   ├── tools/
│   │   └── web_search.py  # Tavily wrapper
│   └── utils/
│       ├── llm.py         # Gemini singleton, retry, model verification
│       ├── cache.py       # JSON file cache — avoids burning free-tier quota
│       ├── cost.py        # Token counting + cost estimation
│       └── timer.py       # Latency context manager
├── data/
│   └── docs/              # .txt files ingested into the knowledge base
├── scripts/
│   ├── build_index.py     # Run once to build the FAISS index
│   └── test_pipeline.py   # End-to-end pipeline smoke test
├── sql/
│   └── schema.sql         # Postgres table definition
├── static/
│   ├── index.html         # Single-page UI served by FastAPI
│   ├── style.css          # Styling — palette, layout, dark theme
│   └── app.js             # Frontend logic — tabs, charts, flow diagram
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and create virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` with your keys:

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) — optional fallback |
| `VERITAS_API_KEY` | Any string you choose — leave blank for local dev |
| `POSTGRES_*` | Your local Postgres credentials |

### 3. Create the Postgres table

```powershell
psql -U postgres -d veritas_agent -f sql/schema.sql
```

### 4. Add documents and build the FAISS index

Drop `.txt` files into `data/docs/`, then:

```powershell
python -m scripts.build_index
# ✅ Indexed N chunks from data/docs
```

The index is saved to `data/faiss_index/` (gitignored).

---

## Run

### Server + UI

```powershell
uvicorn app.main:app --reload --port 8000
```

Opens at `http://localhost:8000`.

### Smoke test (no UI needed)

```powershell
python -m scripts.test_pipeline
```

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/query` | POST | Run a query through the pipeline |
| `/health` | GET | Liveness check |
| `/analytics` | GET | Aggregate stats from Postgres |
| `/analytics/recent` | GET | Most recent queries (newest first) |
| `/analytics/trend` | GET | Chronological cost + grounding trend |
| `/docs` | GET | Auto-generated Swagger UI |

**POST /query**

```json
{ "query": "What are the storage limits on the paid pricing tiers?" }
```

Response includes `answer`, `route`, `grounded`, `failure_reason`, `sources`, `context`, `latency_ms`, `input_tokens`, `output_tokens`, `estimated_cost_usd`.

---

## Dev notes

### LLM response cache

To avoid burning the 20 req/day Gemini free-tier quota during iterative testing, responses are cached to `data/llm_cache.json` (gitignored) keyed by `sha256(prompt)`.

- Clear: `del data\llm_cache.json`
- Disable: set `LLM_CACHE_ENABLED=false` in `.env`
- Cache hits print `💾 Cache hit — skipping API call`

### Model

Currently configured to `gemini-3.6-flash` (stable free-tier as of Sep 2026). If it becomes unavailable, `verify_model_available()` in `app/utils/llm.py` will catch it at startup with a clear error message. Check [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) for the current Flash-tier model name.

### Changing the knowledge base

1. Replace/add `.txt` files in `data/docs/`
2. Delete `data/faiss_index/`
3. Run `python -m scripts.build_index`

---

## UI tabs

- **Ask** — submit a query, see the animated execution-flow diagram (Router → Specialist → Grounding, with retry loop), grounding verdict badge, answer with copy-to-clipboard, sources, and a latency/token/cost stats strip
- **History** — recent queries in a table with route, verdict, cost, latency, and expandable failure reasons
- **Analytics** — aggregate metrics with count-up animation, grounding-rate bar, route split, and a cost/grounding trend chart

Dark mode is available via the toggle in the top bar; the choice is persisted in localStorage.
