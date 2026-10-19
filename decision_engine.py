from tool_manager import tool_manager
from services.tool_registry_bridge import tool_bridge
from services.guardrails import guardrails


# ==========================================
# Decision Engine
# ==========================================

class DecisionEngine:
    """
    مسؤول عن اتخاذ القرار النهائي والتحقق الأمني.
    هل ننفذ Tool ومعاملاتها؟ أم نطلب موافقة أمنية؟ أم نذهب إلى LLM؟
    """

    def __init__(self):
        pass

    # ======================================
    # Decide
    # ======================================

    def decide(self, plan):
        if not isinstance(plan, dict):
            return {"action": "llm"}

        plan_type = plan.get("type")

        # ==================================
        # Tool Action
        # ==================================
        if plan_type == "tool":
            command = plan.get("tool")
            args = plan.get("args", {})

            if not command:
                return {"action": "llm"}

            if not self.can_use_tool(command):
                return {"action": "llm"}

            # فحص بوابة الحوكمة والأمان
            allowed, security_msg = guardrails.verify_action(command, args)
            if not allowed:
                return {
                    "action": "blocked",
                    "tool": command,
                    "reason": security_msg
                }

            # 1. التنفيذ عبر الأدوات الـ 18 المهيكلة أولاً إن وجدت
            if tool_bridge.has_tool(command):
                tool_data = tool_bridge.get_tool(command)
                fn = tool_data.get("fn") or tool_data.get("function")
                try:
                    result = fn(**args) if args else fn()
                    return {
                        "action": "tool",
                        "tool": command,
                        "args": args,
                        "result": result
                    }
                except Exception as e:
                    return {
                        "action": "error",
                        "tool": command,
                        "error": str(e)
                    }

            # 2. الاستدعاء القديم عبر tool_manager
            result = tool_manager.execute(command)
            if result is not None:
                return {
                    "action": "tool",
                    "tool": command,
                    "result": result
                }


        # ==================================
        # Multi-Step Plan
        # ==================================

        if plan_type == "plan":

            return {
                "action": "plan"
            }

        # ==================================
        # LLM
        # ==================================

        return {
            "action": "llm"
        }

    # ======================================
    # Can Use Tool
    # ======================================

    def can_use_tool(self, command):
        if not command:
            return False
        return tool_bridge.has_tool(command) or tool_manager.has_tool(command)


# ==========================================
# Decision Engine Instance
# ==========================================

decision_engine = DecisionEngine()