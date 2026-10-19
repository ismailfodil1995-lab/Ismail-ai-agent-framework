"""
Browser Tool – tools/browser_tool.py
أداة مستقلة لفتح المتصفح والبحث في الويب.
مفصولة عن brain.py لضمان النظافة المعمارية وسهولة الصيانة.
"""

import webbrowser

TOOL_PARAMETERS = {
    "open_browser_url": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "رابط الموقع المراد فتحه بالمتصفح"}
        },
        "required": ["url"]
    },
    "browser_search": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "جملة البحث المراد البحث عنها في الإنترنت"}
        },
        "required": ["query"]
    }
}


def open_browser_url(url: str = "https://google.com", **kwargs) -> str:
    """فتح صفحة ويب داخل المتصفح بطريقة غير حاجزة للنظام."""
    for k in ["url", "link", "website"]:
        if k in kwargs and kwargs[k]:
            url = kwargs[k]
            break
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"SUCCESS: Opened URL '{url}' in browser."
    except Exception as e:
        return f"Error opening browser: {str(e)}"


def browser_search(query: str = "", **kwargs) -> str:
    """البحث السريع في الويب عبر المتصفح وجلب النتائج المباشرة."""
    from web_tool import search_google
    for k in ["query", "q", "search", "topic"]:
        if k in kwargs and kwargs[k]:
            query = kwargs[k]
            break
    if not query:
        return "Error: No search query provided."
    return search_google(query, max_results=5)


# سجل الأدوات المُصدَّرة من هذا الموديول
EXPORTED_TOOLS = {
    "open_browser_url": {
        "name": "Open Browser URL",
        "description": "فتح أي رابط موقع إلكتروني في المتصفح.",
        "parameters": TOOL_PARAMETERS["open_browser_url"],
        "fn": open_browser_url,
        "function": open_browser_url
    },
    "browser_search": {
        "name": "Interactive Browser Search",
        "description": "البحث في الويب ومحركات البحث وجلب أهم النتائج.",
        "parameters": TOOL_PARAMETERS["browser_search"],
        "fn": browser_search,
        "function": browser_search
    }
}
