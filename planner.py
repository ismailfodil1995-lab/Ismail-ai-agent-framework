"""
planner.py - محرك التخطيط الذكي (LLM-First Dynamic Planner)
==============================================================
النهج:
  1. إلغاء الاعتماد كلياً على المطابقة اليدوية الثابتة (Hardcoded) والكلمات المفتاحية.
  2. التخطيط واختيار الأدوات يعتمد بشكل ديناميكي ذكي على الـ LLM.
  3. Sparse Tool Loading: تصنيف الأدوات وتمرير مجموعة الأدوات ذات الصلة فقط
     بناءً على التوجيه الذكي لمنع Token Overflow عند كثرة الأدوات (29+ أداة).
  4. Structured Logging: تسجيل منظم وتفصيلي لكل خطوة (التوجيه، الأدوات المحملة، المدخلات، المخرجات، والزمن).
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from llm.manager import generate
from services.tool_registry_bridge import tool_bridge

logger = logging.getLogger("ai_agent.planner")

# =============================================================================
# Tool Category Map — تصنيف الأدوات الشامل لتفعيل Sparse Tool Loading
# يضم جميع الأدوات المسجلة في الـ Framework
# =============================================================================
TOOL_CATEGORIES: Dict[str, List[str]] = {
    "document": [
        "read_pdf_file", "generate_pdf_report", "summarize_pdf_file",
        "ask_pdf_question", "read_docx_file", "extract_structured_json"
    ],
    "data": [
        "query_duckdb", "inspect_dataset_duckdb", "convert_dataset_duckdb",
        "export_to_csv", "read_excel_file", "generate_excel_report",
        "query_local_db"
    ],
    "web": [
        "search_web", "scrape_web_page", "open_browser_url", "browser_search"
    ],
    "system": [
        "run_system_code", "schedule_task", "list_system_files",
        "read_system_file", "write_system_file"
    ],
    "vision": [
        "extract_text_ocr", "extract_tables_ocr"
    ],
    "communication": [
        "send_email_report", "qualify_lead"
    ],
    "workflow": [
        "compile_dag_workflow", "execute_dag_template", "n8n_orchestrator"
    ]
}


def _select_categories_dynamic(user_input: str) -> List[str]:
    """
    تحديد فئات الأدوات المطلوبة ديناميكياً عبر استدعاء موجه خفيف من الـ LLM (Zero Hardcoded Keywords).
    يختار الفئات الوظيفية الأكثر صلة بالطلب لتطبيق Sparse Tool Loading.
    """
    category_list = list(TOOL_CATEGORIES.keys())
    router_prompt = (
        f"You are a fast intent and domain classifier for an AI agent.\n"
        f"Given the user request, identify 1 to 3 relevant functional tool categories.\n"
        f"Allowed categories: {category_list}\n"
        f"User Request: \"{user_input}\"\n\n"
        f"Output ONLY a JSON array of matching categories. Example: [\"web\", \"data\"].\n"
        f"If the request is purely conversational or unsure, output: [\"general\"]."
    )

    t0 = time.perf_counter()
    try:
        response = generate(router_prompt)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                valid_cats = [c for c in parsed if c in TOOL_CATEGORIES]
                if valid_cats:
                    logger.info(
                        "[Planner][SparseRouter] method=llm_classifier | input='%s' | categories=%s | elapsed_ms=%.1f",
                        user_input[:80], valid_cats, elapsed_ms
                    )
                    return valid_cats

    except Exception as e:
        logger.warning("[Planner][SparseRouter] Router failed with error: %s. Using standard baseline.", e)

    # في حال فشل الاستجابة أو عدم تحديد فئة، نعتمد الفئات الأساسية الشائعة
    default_cats = ["web", "data", "document", "system"]
    logger.info(
        "[Planner][SparseRouter] method=baseline_fallback | input='%s' | categories=%s",
        user_input[:80], default_cats
    )
    return default_cats


def _build_sparse_tool_prompt(relevant_categories: List[str]) -> Tuple[str, List[str]]:
    """
    بناء وصف نصي مُركّز ومُقتصر على الأدوات التابعة للفئات المختارة فقط (Sparse Tool Loading).
    يحمي من تجاوز نافذة السياق (Token Overflow) ويضمن دقة اختيار الـ LLM.
    """
    relevant_tool_keys: List[str] = []
    for cat in relevant_categories:
        relevant_tool_keys.extend(TOOL_CATEGORIES.get(cat, []))

    # إزالة التكرار مع الحفاظ على الترتيب
    seen = set()
    unique_keys = [k for k in relevant_tool_keys if not (k in seen or seen.add(k))]

    all_meta = tool_bridge.get_all_tools_metadata()
    total_tools_count = len(all_meta)

    lines: List[str] = []
    loaded_tools: List[str] = []

    for key in unique_keys:
        if key not in all_meta:
            continue
        info = all_meta[key]
        desc = info.get("description", "")
        props = info.get("parameters", {}).get("properties", {})
        req = info.get("parameters", {}).get("required", [])

        param_parts = []
        for p_name, p_data in props.items():
            p_type = p_data.get("type", "string")
            is_req = "required" if p_name in req else "optional"
            param_parts.append(f"{p_name}: {p_type}[{is_req}]")

        params_str = ", ".join(param_parts) if param_parts else "None"
        lines.append(f"- {key} -> {desc} | Args: [{params_str}]")
        loaded_tools.append(key)

    # في حال لم تتطابق أي أداة، نمرر أول 15 أداة كخيار أمان احتياطي
    if not lines:
        for key, info in list(all_meta.items())[:15]:
            lines.append(f"- {key} -> {info.get('description', '')}")
            loaded_tools.append(key)

    logger.info(
        "[Planner][SparseLoader] loaded=%d/%d tools | categories=%s | active_tools=%s",
        len(loaded_tools), total_tools_count, relevant_categories, loaded_tools
    )
    return "\n".join(lines), loaded_tools


# =============================================================================
# Planner
# =============================================================================

class Planner:
    """
    محرك التخطيط الذكي المعتمد كلياً على الـ LLM:
    - إلغاء المطابقة اليدوية بالكلمات المفتاحية نهائياً.
    - Sparse Tool Loading ديناميكي لتوفير استهلاك الـ Tokens ومنع Token Overflow.
    - Structured Logging شامل لتسهيل المراقبة والـ Debugging.
    """

    def _ai_plan(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        استدعاء الـ LLM لبناء خطة العمل الذكية بناءً على أدوات الـ Sparse المحددة.
        """
        # 1. التوجيه الذكي واختيار الفئات ذات الصلة فقط
        categories = _select_categories_dynamic(user_input)

        # 2. توليد موجه الأدوات المختصرة
        tools_text, loaded_tools = _build_sparse_tool_prompt(categories)

        planning_prompt = f"""You are the central intelligent planner of "Ismail Smart Agent".
Analyze the user request and determine the best action or tool sequence.

Available Relevant Tools:
{tools_text}

User Request:
{user_input}

STRICT INSTRUCTIONS:
- Return ONLY valid JSON, absolutely no extra explanation or markdown quotes outside JSON.
- If a tool is required, select ONLY from the Available Relevant Tools listed above.
- Provide exact arguments matching the parameter names.
- If the user request is a general question, greeting, or explanation needing NO tool, return {{"type": "llm"}}.

JSON OUTPUT FORMATS:
1. Single Tool:
{{
    "type": "tool",
    "tool": "exact_tool_name",
    "args": {{"param_name": "value"}}
}}

2. Multi-Step Plan:
{{
    "type": "plan",
    "steps": [
        {{"tool": "first_tool", "args": {{}}}},
        {{"tool": "second_tool", "args": {{}}}}
    ]
}}

3. Conversational / Direct Answer:
{{
    "type": "llm"
}}
"""

        t_start = time.perf_counter()
        try:
            raw_response = generate(planning_prompt)
            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)

            logger.debug(
                "[Planner][LLM] elapsed_ms=%.1f | raw_snippet='%s'",
                elapsed_ms, raw_response[:120].replace("\n", " ")
            )

            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if not match:
                logger.warning("[Planner][LLM] No JSON object found in response.")
                return None

            data = json.loads(match.group())
            if not isinstance(data, dict) or "type" not in data:
                logger.warning("[Planner][LLM] Invalid plan format: %s", data)
                return None

            return data

        except json.JSONDecodeError as e:
            logger.error("[Planner][LLM] JSON parse failure: %s", e)
            return None
        except Exception as e:
            logger.error("[Planner][LLM] Unexpected error during planning: %s", e)
            return None

    def make_plan(self, user_input: str) -> Dict[str, Any]:
        """
        نقطة الدخول الرئيسية للتخطيط الذكي.
        تعتمد بالكامل على ديناميكية الـ LLM مع Sparse Tool Loading وتسجيل Structured Logs.
        """
        original = user_input.strip()
        t_start = time.perf_counter()

        logger.info("[Planner][MakePlan] START | input='%s'", original[:100])

        plan = self._ai_plan(original)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)

        if plan:
            plan_type = plan.get("type", "unknown")
            if plan_type == "tool":
                logger.info(
                    "[Planner][MakePlan] SUCCESS | type=tool | tool='%s' | args=%s | total_elapsed_ms=%.1f",
                    plan.get("tool"), plan.get("args", {}), elapsed_ms
                )
            elif plan_type == "plan":
                steps = plan.get("steps", [])
                step_tools = [s.get("tool", "?") for s in steps]
                logger.info(
                    "[Planner][MakePlan] SUCCESS | type=plan | steps_count=%d | tools=%s | total_elapsed_ms=%.1f",
                    len(steps), step_tools, elapsed_ms
                )
            else:
                logger.info(
                    "[Planner][MakePlan] SUCCESS | type=llm (pure conversational) | total_elapsed_ms=%.1f",
                    elapsed_ms
                )
            return plan

        # Fallback آمن عند أي تعثر في التخطيط
        logger.warning(
            "[Planner][MakePlan] FALLBACK | type=llm | total_elapsed_ms=%.1f",
            elapsed_ms
        )
        return {"type": "llm"}


# Singleton Instance
planner = Planner()