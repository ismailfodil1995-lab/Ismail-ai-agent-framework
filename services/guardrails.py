"""
Guardrails Gateway: بوابة الحوكمة والأمان والموافقة البشرية (Human-in-the-Loop)
"""
import sys
import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import CRITICAL_TOOLS, GUARDRAILS_MODE


class GuardrailsGateway:
    """
    بوابة أمان وسيطة تعترض استدعاءات الأدوات الحرجة
    وتضمن التحقق من الصلاحيات والموافقة البشرية قبل الإجراءات الحساسة
    """

    def __init__(self, mode: str = GUARDRAILS_MODE, critical_tools: Optional[List[str]] = None):
        self.mode = mode
        self.critical_tools = critical_tools or CRITICAL_TOOLS
        self.audit_log: List[Dict[str, Any]] = []
        self._custom_approver: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def set_custom_approver(self, approver_fn: Callable[[str, Dict[str, Any]], bool]) -> None:
        """تعيين دالة مخصصة لطلب الموافقة (مثلاً لبوت تيليجرام أو واجهة ويب)"""
        self._custom_approver = approver_fn

    def is_critical(self, tool_name: str) -> bool:
        """هل الأداة مصنفة ضمن العمليات ذات الحساسية العالية؟"""
        return tool_name in self.critical_tools

    def verify_action(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        context_description: str = ""
    ) -> Tuple[bool, str]:
        """
        فحص العملية قبل تنفيذها:
        - إذا لم تكن حرجة: يُسمح فوراً.
        - إذا كانت حرجة: يتم تطبيق سياسة الأمان المختارة (auto / ask / strict).
        """
        args = args or {}
        timestamp = datetime.datetime.now().isoformat()

        if not self.is_critical(tool_name):
            return True, "Safe Action: Auto-approved."

        # نمط "auto": السماح مع التوثيق في سجل التدقيق الأمني
        if self.mode == "auto":
            record = {
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "decision": "APPROVED",
                "policy": "auto"
            }
            self.audit_log.append(record)
            return True, "Policy auto-approval granted with audit logging."

        # نمط "strict": الحظر التام للأدوات الحرجة
        if self.mode == "strict":
            record = {
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "decision": "BLOCKED",
                "policy": "strict"
            }
            self.audit_log.append(record)
            return False, f"SECURITY ALERT: Tool '{tool_name}' is blocked by strict policy."

        # نمط "ask": طلب الموافقة البشرية (Human-in-the-Loop)
        # 1. إذا وُجدت دالة موافقة مخصصة (مثل واجهة محادثة بوت)
        if self._custom_approver:
            approved = self._custom_approver(tool_name, args)
            decision = "APPROVED" if approved else "REJECTED"
            self.audit_log.append({
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "decision": decision,
                "policy": "custom_ask"
            })
            return approved, f"Action {decision.lower()} by custom reviewer."

        # 2. إذا كنا في بيئة طرفية تفاعلية CLI
        if sys.stdin and sys.stdin.isatty():
            print("\n" + "=" * 55)
            print("🛡️  [SECURITY GUARDRAIL] Human Approval Required")
            print(f"Action: Execute critical tool '{tool_name}'")
            print(f"Arguments: {args}")
            if context_description:
                print(f"Context: {context_description}")
            print("=" * 55)

            try:
                choice = input("Do you approve this execution? (y/N): ").strip().lower()
                approved = choice in ["y", "yes", "موافق", "نعم"]
            except Exception:
                approved = False

            decision = "APPROVED" if approved else "REJECTED"
            self.audit_log.append({
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "decision": decision,
                "policy": "interactive_cli"
            })
            return approved, f"Action {decision.lower()} by user in CLI."

        # في حال عدم وجود طرفية تفاعلية في وضع ask، يُمنع التنفيذ حرصاً على الأمان
        self.audit_log.append({
            "timestamp": timestamp,
            "tool": tool_name,
            "args": args,
            "decision": "REJECTED",
            "policy": "non_interactive_fallback"
        })
        return False, f"Action for '{tool_name}' rejected: Non-interactive session cannot grant approval."

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """الحصول على سجل كافة القرارات الأمنية المسجلة"""
        return list(self.audit_log)


# Singleton instance
guardrails = GuardrailsGateway()
