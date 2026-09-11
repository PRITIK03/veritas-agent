from tavily import TavilyClient
from app.config import settings

_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def web_search(query: str, max_results: int = 3):
    response = _client.search(query=query, max_results=max_results)
    return [
        {"text": r.get("content", ""),
         "source": {"url": r.get("url", ""), "title": r.get("title", "")}}
        for r in response.get("results", [])
    ]