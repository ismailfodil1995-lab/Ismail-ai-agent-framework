"""
Plugin & Tools Loader
الإصدار 2.0 – يدعم الآن التحميل التلقائي من EXPORTED_TOOLS لكل موديول مستقل.
"""

# قاموس لتخزين كافة الأدوات المتاحة للنظام
AVAILABLE_TOOLS = {}


def register_tool(name: str, description: str):
    def decorator(func):
        AVAILABLE_TOOLS[name] = {
            "fn": func,
            "description": description
        }
        return func
    return decorator


def _load_module_tools(module):
    """تحميل EXPORTED_TOOLS من أي موديول أداة مستقل ودمجها في AVAILABLE_TOOLS."""
    exported = getattr(module, "EXPORTED_TOOLS", None)
    if exported and isinstance(exported, dict):
        AVAILABLE_TOOLS.update(exported)


# ─── تحميل الأدوات الكلاسيكية (الموديولات القديمة) ──────────────────────────
import tools.web_scraper
import tools.web_search
import tools.data_exporter
import tools.pdf_reader
import tools.pdf_generator
import tools.pdf_ai_tools
import tools.lead_qualifier
import tools.docx_tool
import tools.email_sender
import tools.json_extractor
import tools.db_tool
import tools.dag_tool

# ─── تحميل الأدوات المفككة حديثاً من brain.py (المعمارية الجديدة) ────────────
import tools.excel_tool
import tools.scheduler_tool
import tools.system_tool
import tools.browser_tool
import tools.ocr_tool
import tools.duckdb_tool

_load_module_tools(tools.excel_tool)
_load_module_tools(tools.scheduler_tool)
_load_module_tools(tools.system_tool)
_load_module_tools(tools.browser_tool)
_load_module_tools(tools.ocr_tool)
_load_module_tools(tools.duckdb_tool)