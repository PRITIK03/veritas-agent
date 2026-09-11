from langgraph.graph import StateGraph, START, END
from app.graph.state import GraphState
from app.graph.router import route_node
from app.graph.specialists import rag_node, web_search_node
from app.graph.grounding import grounding_node
from app.utils.encoding import force_utf8_output

force_utf8_output()


def retry_node(state: GraphState) -> GraphState:
    """Prepare a single broader-retrieval retry after a grounding failure."""
    state["retry_count"] = state.get("retry_count", 0) + 1
    print(f"🔄 Grounding failed — retrying with broader retrieval (attempt {state['retry_count'] + 1})")
    return state


def after_grounding(state: GraphState) -> str:
    if not state.get("grounded") and state.get("retry_count", 0) == 0:
        return "retry"
    return "end"


def build_pipeline():
    graph = StateGraph(GraphState)
    graph.add_node("router", route_node)
    graph.add_node("rag", rag_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("grounding", grounding_node)
    graph.add_node("retry", retry_node)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {"rag": "rag", "web_search": "web_search"},
    )
    graph.add_edge("rag", "grounding")
    graph.add_edge("web_search", "grounding")
    graph.add_conditional_edges(
        "grounding",
        after_grounding,
        {"retry": "retry", "end": END},
    )
    graph.add_conditional_edges(
        "retry",
        lambda state: state["route"],
        {"rag": "rag", "web_search": "web_search"},
    )

    return graph.compile()


pipeline = build_pipeline()
