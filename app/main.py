from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from app.config import settings
from app.graph.pipeline import pipeline
from app.utils.timer import timer
from app.utils.cost import estimate_cost
from app.utils.llm import verify_model_available
from app.db import log_query, get_analytics_summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast and loudly on boot if the configured model isn't usable,
    # rather than discovering it on the first user request. A transient
    # rate-limit (429) is not a misconfiguration, so it degrades to a warning
    # instead of preventing the server from starting.
    try:
        verify_model_available()
    except RuntimeError as e:
        cause_text = f"{e} {getattr(e, '__cause__', '')}".lower()
        if "429" in cause_text or "resource_exhausted" in cause_text or "quota" in cause_text:
            print("⚠️ Startup model check hit a rate limit — server will start, "
                  "but requests may fail until quota resets.")
        else:
            raise
    yield


app = FastAPI(title="Veritas Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    expected = settings.VERITAS_API_KEY
    if not expected:
        # No key configured — allow (local dev). Set VERITAS_API_KEY to enforce.
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=settings.MAX_QUERY_LENGTH)


class QueryResponse(BaseModel):
    answer: str
    route: str
    grounded: bool
    failure_reason: Optional[str]
    sources: List[Dict]
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class RouteCounts(BaseModel):
    rag: int
    web_search: int


class AnalyticsResponse(BaseModel):
    total_queries: int
    grounding_success_rate_pct: float
    avg_latency_ms: float
    avg_estimated_cost_usd: float
    total_estimated_cost_usd: float
    route_counts: RouteCounts


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest, _: None = Depends(require_api_key)):
    initial_state = {
        "query": req.query, "route": "", "context": [], "sources": [],
        "answer": "", "grounded": False, "failure_reason": None,
        "input_tokens": 0, "output_tokens": 0, "retry_count": 0,
    }

    with timer() as t:
        result = pipeline.invoke(initial_state)

    cost = estimate_cost(result["input_tokens"], result["output_tokens"])

    log_query(
        query=req.query, route=result["route"], answer=result["answer"],
        sources=result["sources"], grounded=result["grounded"],
        failure_reason=result["failure_reason"], latency_ms=t["latency_ms"],
        input_tokens=result["input_tokens"], output_tokens=result["output_tokens"],
        estimated_cost_usd=cost,
    )

    return QueryResponse(
        answer=result["answer"], route=result["route"], grounded=result["grounded"],
        failure_reason=result["failure_reason"], sources=result["sources"],
        latency_ms=t["latency_ms"], input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"], estimated_cost_usd=cost,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/analytics", response_model=AnalyticsResponse)
def analytics_endpoint(_: None = Depends(require_api_key)):
    return get_analytics_summary()


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/")
def root():
    return {"service": "Veritas Agent", "status": "running", "docs": "/docs"}
