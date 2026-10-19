"""
Reflection Engine: محرك التفكير الارتجاعي والتصحيح الذاتي للأدوات (Self-Healing Loop)
"""
import json
import os
import re
from typing import Any, Dict, Optional, Tuple

from config import ENABLE_SELF_HEALING, MAX_REFLECTION_ATTEMPTS
from llm.manager import generate
from services.tool_registry_bridge import tool_bridge


class ReflectionEngine:
    """
    يقوم بتحليل أخطاء تنفيذ الأدوات وتقديم مدخلات مصححة
    لتحقيق مبدأ التعافي الذاتي (Self-Healing) دون توقف المسار
    """

    def __init__(self, max_attempts: int = MAX_REFLECTION_ATTEMPTS):
        self.max_attempts = max_attempts

    def _heuristic_fix(self, tool_name: str, failed_args: Dict[str, Any], error_message: str) -> Optional[Dict[str, Any]]:
        """
        إصلاحات أولية سريعة وخفيفة للمشاكل الشائعة قبل أو بالتوازي مع استدعاء الـ LLM
        """
        fixed = dict(failed_args) if failed_args else {}

        # 1. إصلاح روابط الويب الناقصة
        if tool_name in ["scrape_web_page", "open_browser_url"]:
            url = fixed.get("url", "")
            if url and not url.startswith("http://") and not url.startswith("https://"):
                fixed["url"] = "https://" + url
                return fixed

        # 2. إصلاح امتدادات ملفات الإكسل أو التقارير
        if tool_name in ["generate_excel_report", "read_excel_file"]:
            filename = fixed.get("filename", "")
            if filename and not filename.endswith(".xlsx") and not filename.endswith(".xls"):
                fixed["filename"] = filename + ".xlsx"
                return fixed

        # 3. إصلاح امتدادات ملفات PDF
        if tool_name in ["read_pdf_file", "summarize_pdf_file", "ask_pdf_question", "generate_pdf_report"]:
            file_path = fixed.get("file_path") or fixed.get("filename", "")
            if file_path and not file_path.endswith(".pdf"):
                file_path += ".pdf"
                if "file_path" in fixed:
                    fixed["file_path"] = file_path
                if "filename" in fixed:
                    fixed["filename"] = file_path
                return fixed

        return None

    def reflect_and_correct(
        self,
        tool_name: str,
        failed_args: Dict[str, Any],
        error_message: str,
        context_hint: str = ""
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        تحليل سبب فشل الأداة واسترجاع معاملات مصححة
        ترجع: (is_corrected, new_args, explanation)
        """
        if not ENABLE_SELF_HEALING:
            return False, failed_args, "Self-healing is disabled in config."

        # 1. فحص الكشف الإرشادي السريع
        heuristic = self._heuristic_fix(tool_name, failed_args, error_message)
        if heuristic and heuristic != failed_args:
            return True, heuristic, "Heuristic self-correction applied."

        # 2. التحليل الذكي عبر الـ LLM
        tool_meta = tool_bridge.get_all_tools_metadata().get(tool_name, {})
        spec_text = json.dumps(tool_meta.get("parameters", {}), ensure_ascii=False)

        prompt = f"""
You are the Self-Healing Reflection Engine of an AI Agent Framework.
A tool execution failed, and your job is to fix the parameters so the tool succeeds.

Tool Name: {tool_name}
Tool Description: {tool_meta.get('description', '')}
Tool Parameter Schema:
{spec_text}

Failed Arguments:
{json.dumps(failed_args, ensure_ascii=False)}

Error Message Received:
{error_message}

Context / Goal:
{context_hint}

Instructions:
1. Analyze the exact error message (e.g. missing required field, bad URL, wrong file path, invalid type).
2. If you can fix the arguments to make the tool call succeed, return JSON:
{{
    "status": "fixed",
    "corrected_args": {{ ... }},
    "explanation": "Brief explanation of what was corrected"
}}
3. If the error is fatal and cannot be fixed by changing arguments (e.g. external network completely down, file physically absent), return:
{{
    "status": "unfixable",
    "explanation": "Why this cannot be fixed"
}}

Return ONLY valid JSON.
"""
        try:
            response = generate(prompt)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                return False, failed_args, "Failed to parse reflection JSON."

            data = json.loads(match.group())
            if data.get("status") == "fixed" and isinstance(data.get("corrected_args"), dict):
                return True, data["corrected_args"], data.get("explanation", "Corrected by LLM reflection.")
            else:
                return False, failed_args, data.get("explanation", "Marked unfixable by reflection.")

        except Exception as e:
            return False, failed_args, f"Reflection exception: {str(e)}"


# Singleton instance
reflection_engine = ReflectionEngine()
