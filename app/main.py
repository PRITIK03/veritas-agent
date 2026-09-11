from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.graph.pipeline import pipeline
from app.utils.timer import timer
from app.utils.cost import estimate_cost
from app.db import log_query, get_analytics_summary

app = FastAPI(title="Veritas Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


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
def query_endpoint(req: QueryRequest):
    initial_state = {
        "query": req.query, "route": "", "context": [], "sources": [],
        "answer": "", "grounded": False, "failure_reason": None,
        "input_tokens": 0, "output_tokens": 0,
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
def analytics_endpoint():
    return get_analytics_summary()
