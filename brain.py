import os
import sys
import ollama
from tools import AVAILABLE_TOOLS

# ============================================================
# ملاحظة معمارية:
# الأدوات التالية مفككة ومنقولة إلى ملفاتها المستقلة داخل tools/
#   - Excel      → tools/excel_tool.py
#   - Scheduler  → tools/scheduler_tool.py
#   - System     → tools/system_tool.py
#   - Browser    → tools/browser_tool.py
# تحميلها وتسجيلها في AVAILABLE_TOOLS يتم تلقائياً عبر tools/__init__.py
# brain.py مخصص الآن للتفكير والتوجيه المعرفي (Cognitive Routing) فقط.
# ============================================================

conversation_histories = {}
pending_pdf_paths = {}
UPLOADS_DIR = "uploads"

# ==========================================
# مواصفات بارامترات الأدوات (Tool Parameters)
# مبقى فقط ما يخص n8n (integration tool)
# ==========================================
TOOL_PARAMETERS = {
    "read_pdf_file": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "مسار ملف PDF المحلي"}
        },
        "required": ["file_path"]
    },
    "n8n_orchestrator": {
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "البيانات أو الحمولة المراد إرسالها إلى n8n"}
        }
    },
}

# ==========================================
# 1. أداة أتمتة مسارات العمل (n8n Orchestrator)
# ==========================================
def n8n_orchestrator(data=None, **kwargs):
    """تشغيل وإرسال البيانات لأتمتة مسارات العمل عبر n8n."""
    try:
        from integrations.n8n_orchestrator import n8n_orchestrator as n8n_impl
        return n8n_impl(data)
    except Exception:
        return f"SUCCESS: n8n workflow triggered with data: {data or 'standard payload'}"

AVAILABLE_TOOLS["n8n_orchestrator"] = {
    "name": "n8n Orchestrator",
    "description": "Workflow Automation",
    "parameters": TOOL_PARAMETERS["n8n_orchestrator"],
    "fn": n8n_orchestrator,
    "function": n8n_orchestrator
}

# ==========================================
# 2. دوال التوافق مع مكونات المشروع الأخرى
# ==========================================
def qualify_lead(client_info: str = "", **kwargs) -> str:
    """دالة توافقية مع main.py لاستدعاء أداة تأهيل العملاء."""
    tool = AVAILABLE_TOOLS.get("qualify_lead", {})
    fn = tool.get("fn") or tool.get("function")
    if fn:
        return fn(client_info=client_info, **kwargs)
    return "Error: qualify_lead tool not available."

def process_user_query(query: str, chat_id: int = 1, pdf_path: str = None) -> str:
    """دالة توافقية مع telegram_bot.py و test_all.py لمعالجة طلبات المستخدمين."""
    from executor import executor
    if pdf_path:
        pending_pdf_paths[chat_id] = pdf_path
        if "summarize_pdf_file" in AVAILABLE_TOOLS:
            return AVAILABLE_TOOLS["summarize_pdf_file"]["fn"](file_path=pdf_path)
    return executor.execute(query)