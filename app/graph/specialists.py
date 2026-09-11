import time
from app.graph.state import GraphState
from app.rag.retriever import retrieve
from app.tools.web_search import web_search
from app.utils.cache import cached_llm_invoke
from app.utils.cost import count_tokens

ANSWER_PROMPT = """Answer the user's question using ONLY the context below.
If the context doesn't contain enough information, say so explicitly rather than guessing.

Context:
{context}

Question: {query}

Answer:
"""

def _answer_from(state, results):
    context_text = "\n\n".join(r["text"] for r in results)
    sources = [r["source"] for r in results]
    prompt = ANSWER_PROMPT.format(context=context_text, query=state["query"])
    _t0 = time.perf_counter()
    answer = cached_llm_invoke(prompt)
    print(f"[TIMING] specialists llm.invoke(): {(time.perf_counter() - _t0)*1000:.0f} ms")

    state["context"] = [r["text"] for r in results]
    state["sources"] = sources
    state["answer"] = answer
    state["input_tokens"] = state.get("input_tokens", 0) + count_tokens(prompt)
    state["output_tokens"] = state.get("output_tokens", 0) + count_tokens(answer)
    return state

def rag_node(state: GraphState) -> GraphState:
    return _answer_from(state, retrieve(state["query"], k=3))

def web_search_node(state: GraphState) -> GraphState:
    return _answer_from(state, web_search(state["query"], max_results=3))
