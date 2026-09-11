from langgraph.graph import StateGraph, START, END
from app.graph.state import GraphState
from app.graph.router import route_node
from app.graph.specialists import rag_node, web_search_node
from app.graph.grounding import grounding_node

def build_pipeline():
    graph = StateGraph(GraphState)
    graph.add_node("router", route_node)
    graph.add_node("rag", rag_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("grounding", grounding_node)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {"rag": "rag", "web_search": "web_search"},
    )
    graph.add_edge("rag", "grounding")
    graph.add_edge("web_search", "grounding")
    graph.add_edge("grounding", END)

    return graph.compile()

pipeline = build_pipeline()