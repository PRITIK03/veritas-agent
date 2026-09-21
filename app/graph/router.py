from app.graph.state import GraphState
from app.utils.cache import cached_llm_invoke
from app.utils.cost import count_tokens

ROUTER_PROMPT = """You are a routing agent. Decide whether the user's query should be
answered using an internal knowledge base (RAG) or a live web search.

Use "rag" for questions the internal docs likely cover.
Use "web_search" for anything needing current/live information.

Respond with exactly one word: "rag" or "web_search".

Query: {query}
"""

def route_node(state: GraphState) -> GraphState:
    prompt = ROUTER_PROMPT.format(query=state["query"])
    try:
        decision = cached_llm_invoke(prompt).lower()
    except TimeoutError:
        print("⏱️ Router LLM call timed out — defaulting to safe fallback route 'rag'.")
        state["route"] = "rag"
        state["input_tokens"] = state.get("input_tokens", 0) + count_tokens(prompt)
        return state

    state["route"] = "web_search" if "web_search" in decision else "rag"
    state["input_tokens"] = state.get("input_tokens", 0) + count_tokens(prompt)
    state["output_tokens"] = state.get("output_tokens", 0) + count_tokens(decision)
    return state
