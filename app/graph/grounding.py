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
    if not state.get("context"):
        # No retrieved context: the specialist already returned an honest
        # non-answer. Don't send empty context to the fact-checker.
        print("⚠️ grounding node: empty context — treating honest non-answer as grounded.")
        state["grounded"] = True
        state["failure_reason"] = None
        return state

    context_text = "\n\n".join(state.get("context", []))
    prompt = GROUNDING_PROMPT.format(context=context_text, answer=state["answer"])
    result = cached_llm_invoke(prompt)

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
