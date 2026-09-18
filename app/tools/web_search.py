from tavily import TavilyClient

from app.config import settings

_client = None


def _get_client():
    """Lazily build the Tavily client so a missing API key doesn't crash
    module import (and therefore the whole app) before the first web search."""
    global _client
    if _client is None:
        if not settings.TAVILY_API_KEY:
            return None
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


def web_search(query: str, max_results: int = 3):
    client = _get_client()
    if client is None:
        print("⚠️ TAVILY_API_KEY not set — web search unavailable, returning no results.")
        return []
    try:
        response = client.search(query=query, max_results=max_results)
    except Exception as e:
        print(f"⚠️ Web search failed: {e} — falling back to no results.")
        return []
    return [
        {"text": r.get("content", ""),
         "source": {"url": r.get("url", ""), "title": r.get("title", "")}}
        for r in response.get("results", [])
    ]