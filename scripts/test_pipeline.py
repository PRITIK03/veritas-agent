from app.graph.pipeline import pipeline
from app.utils.timer import timer
from app.utils.cost import estimate_cost
from app.utils.llm import verify_model_available
from app.db import log_query

def run(query: str):
    initial_state = {
        "query": query,
        "route": "",
        "context": [],
        "sources": [],
        "answer": "",
        "grounded": False,
        "failure_reason": None,
        "input_tokens": 0,
        "output_tokens": 0,
    }

    with timer() as t:
        result = pipeline.invoke(initial_state)

    cost = estimate_cost(result["input_tokens"], result["output_tokens"])

    print("\n" + "=" * 60)
    print(f"QUERY:      {query}")
    print(f"ROUTE:      {result['route']}")
    print(f"ANSWER:     {result['answer']}")
    print(f"GROUNDED:   {result['grounded']}")
    print(f"FAILURE:    {result['failure_reason']}")
    print(f"SOURCES:    {result['sources']}")
    print(f"LATENCY:    {t['latency_ms']} ms")
    print(f"TOKENS:     in={result['input_tokens']} out={result['output_tokens']}")
    print(f"EST. COST:  ${cost}")
    print("=" * 60)

    log_query(
        query=query,
        route=result["route"],
        answer=result["answer"],
        sources=result["sources"],
        grounded=result["grounded"],
        failure_reason=result["failure_reason"],
        latency_ms=t["latency_ms"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        estimated_cost_usd=cost,
    )
    print("✅ Logged to Postgres\n")

if __name__ == "__main__":
    from app.config import settings as _settings
    print(f"GEMINI_MODEL loaded: {_settings.GEMINI_MODEL}")

    verify_model_available()

    # Should hit RAG — it's covered by your Nimbus Cloud docs
    run("What are the storage limits on the paid pricing tiers?")

    # Should hit web_search — nothing in your docs covers this
    run("What's the latest news about Google Gemini 3?")

    # Should hit RAG but likely trigger NOT_GROUNDED — docs won't have this
    run("What is Nimbus Cloud's refund policy for annual plans cancelled after 11 months?")