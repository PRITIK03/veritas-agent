from typing import TypedDict, List, Dict, Optional

class GraphState(TypedDict):
    query: str
    route: str
    context: List[str]
    sources: List[Dict]
    answer: str
    grounded: bool
    failure_reason: Optional[str]
    input_tokens: int
    output_tokens: int