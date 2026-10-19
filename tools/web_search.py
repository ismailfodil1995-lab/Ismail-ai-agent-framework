from web_tool import search_google
from tools import register_tool


@register_tool(
    name="search_web",
    description="البحث الحقيقي في الإنترنت وجلب نتائج حديثة عن أي موضوع أو سؤال."
)
def search_web(query: str = "", max_results: int = 5, **kwargs) -> str:
    for key in ["query", "q", "search", "question", "topic"]:
        if key in kwargs and kwargs[key]:
            query = kwargs[key]
            break

    if not query:
        return "Error: No search query provided."

    try:
        max_results = int(max_results)
    except (TypeError, ValueError):
        max_results = 5

    max_results = max(1, min(max_results, 10))
    return search_google(query, max_results=max_results)
