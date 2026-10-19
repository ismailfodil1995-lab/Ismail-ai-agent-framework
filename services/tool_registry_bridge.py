"""
Tool Registry Bridge: جسر الربط الموحد بين قاموس الأدوات الـ 18 ومحركات التخطيط والتنفيذ
"""
import inspect
from typing import Any, Dict, List, Optional, Tuple

AVAILABLE_TOOLS = {}
TOOL_PARAMETERS = {}


class ToolRegistryBridge:
    """
    يقوم بفحص واستخراج مخططات الـ 18 أداة ديناميكياً
    وتوليد مواصفات المعاملات بصيغة مهيكلة للـ LLM
    """

    def __init__(self):
        pass

    @property
    def tools(self) -> Dict[str, Any]:
        global AVAILABLE_TOOLS
        if not AVAILABLE_TOOLS:
            try:
                import brain
                if hasattr(brain, "AVAILABLE_TOOLS") and brain.AVAILABLE_TOOLS:
                    AVAILABLE_TOOLS = brain.AVAILABLE_TOOLS
            except Exception:
                pass
        if not AVAILABLE_TOOLS:
            try:
                import tools
                if hasattr(tools, "AVAILABLE_TOOLS") and tools.AVAILABLE_TOOLS:
                    AVAILABLE_TOOLS = tools.AVAILABLE_TOOLS
            except Exception:
                pass
        return AVAILABLE_TOOLS or {}

    @property
    def parameters(self) -> Dict[str, Any]:
        global TOOL_PARAMETERS
        if not TOOL_PARAMETERS:
            try:
                import brain
                if hasattr(brain, "TOOL_PARAMETERS") and brain.TOOL_PARAMETERS:
                    TOOL_PARAMETERS = brain.TOOL_PARAMETERS
            except Exception:
                pass
        return TOOL_PARAMETERS or {}

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        return self.tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self.tools

    def get_all_tools_metadata(self) -> Dict[str, Dict[str, Any]]:
        """استخراج تفاصيل ومخطط كل أداة من الأدوات الـ 18 المسجلة"""
        metadata = {}
        for tool_name, tool_data in self.tools.items():
            desc = tool_data.get("description", "No description available.")
            display_name = tool_data.get("name", tool_name)
            params = tool_data.get("parameters") or self.parameters.get(tool_name, {})
            
            # إذا لم تكن البارامترات محددة في TOOL_PARAMETERS، نستخرجها بالانعكاس البرمجي (Inspection)
            if not params and "fn" in tool_data:
                sig = inspect.signature(tool_data["fn"])
                prop_dict = {}
                req_list = []
                for p_name, p_param in sig.parameters.items():
                    if p_name in ["kwargs", "args"]:
                        continue
                    p_type = "string"
                    if p_param.annotation is int:
                        p_type = "integer"
                    elif p_param.annotation is list:
                        p_type = "array"
                    elif p_param.annotation is dict:
                        p_type = "object"
                    elif p_param.annotation is bool:
                        p_type = "boolean"

                    prop_dict[p_name] = {"type": p_type}
                    if p_param.default == inspect.Parameter.empty:
                        req_list.append(p_name)

                params = {
                    "type": "object",
                    "properties": prop_dict,
                    "required": req_list
                }

            metadata[tool_name] = {
                "name": display_name,
                "description": desc,
                "parameters": params
            }
        return metadata

    def build_tool_prompt_description(self) -> str:
        """
        توليد وصف نصي موحد ودقيق لكافة الأدوات الـ 18
        لتزويد الـ Planner و LLMManager به في الـ Prompts
        """
        meta = self.get_all_tools_metadata()
        lines = []
        for tool_name, info in sorted(meta.items()):
            desc = info["description"]
            props = info.get("parameters", {}).get("properties", {})
            req = info.get("parameters", {}).get("required", [])

            param_str_parts = []
            for prop_name, prop_data in props.items():
                p_type = prop_data.get("type", "string")
                is_req = "required" if prop_name in req else "optional"
                p_desc = prop_data.get("description", "")
                suffix = f" ({p_desc})" if p_desc else ""
                param_str_parts.append(f"{prop_name}: {p_type}[{is_req}]{suffix}")

            params_formatted = ", ".join(param_str_parts) if param_str_parts else "None"
            lines.append(f"- {tool_name} -> {desc} | Args: [{params_formatted}]")

        return "\n".join(lines)

    def validate_tool_args(self, tool_name: str, args: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
        """التحقق من صحة واكتمال المعاملات المطلوبة للأداة"""
        if not self.has_tool(tool_name):
            return False, f"Tool '{tool_name}' is not in AVAILABLE_TOOLS."

        args = args or {}
        tool_meta = self.get_all_tools_metadata().get(tool_name, {})
        required_fields = tool_meta.get("parameters", {}).get("required", [])

        for req in required_fields:
            if req not in args or args[req] is None or str(args[req]).strip() == "":
                return False, f"Missing required parameter '{req}' for tool '{tool_name}'."

        return True, "Valid"

    def match_tool_name(self, text: str) -> Optional[str]:
        """مطابقة ذكية لاسم الأداة من النص المدخل"""
        clean = text.strip().lower()
        if clean in self.tools:
            return clean

        for tool_name in self.tools:
            if tool_name in clean:
                return tool_name

        # مطابقة دلالية سريعة لبعض الأسماء الشائعة
        aliases = {
            "search": "search_web",
            "google": "search_web",
            "scrape": "scrape_web_page",
            "pdf_read": "read_pdf_file",
            "pdf_summarize": "summarize_pdf_file",
            "excel_generate": "generate_excel_report",
            "excel_read": "read_excel_file",
            "csv": "export_to_csv",
            "n8n": "n8n_orchestrator",
            "schedule": "schedule_task",
            "qualify": "qualify_lead"
        }
        for alias, target in aliases.items():
            if alias in clean and target in self.tools:
                return target

        return None


# Singleton instance
tool_bridge = ToolRegistryBridge()
