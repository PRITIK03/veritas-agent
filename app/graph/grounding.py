import time
from app.graph.state import GraphState
from app.utils.cache import cached_llm_invoke
from app.utils.cost import count_tokens

GROUNDING_PROMPT = """You are a strict fact-checker. Given the CONTEXT and the ANSWER,
determine if the ANSWER is fully supported by the CONTEXT.

Respond in exactly this format:
VERDICT: <GROUNDED or NOT_GROUNDED>
REASON: <one short sentence>

Context:
{context}

Answer:
{answer}
"""

def grounding_node(state: GraphState) -> GraphState:
    context_text = "\n\n".join(state.get("context", []))
    prompt = GROUNDING_PROMPT.format(context=context_text, answer=state["answer"])
    _t0 = time.perf_counter()
    result = cached_llm_invoke(prompt)
    print(f"[TIMING] grounding llm.invoke(): {(time.perf_counter() - _t0)*1000:.0f} ms")

    grounded = "NOT_GROUNDED" not in result.upper()
    reason = ""
    for line in result.splitlines():
        if line.upper().startswith("REASON"):
            reason = line.split(":", 1)[-1].strip()

    state["grounded"] = grounded
    state["failure_reason"] = None if grounded else reason
    state["input_tokens"] = state.get("input_tokens", 0) + count_tokens(prompt)
    state["output_tokens"] = state.get("output_tokens", 0) + count_tokens(result)
    return state
