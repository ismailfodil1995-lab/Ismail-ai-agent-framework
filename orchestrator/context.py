"""
ExecutionContext: حاوية الحالة المشتركة لطبقة الأتمتة المتقدمة
"""
import uuid
import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ExecutionRecord:
    """سجل يوثق تفاصيل تنفيذ كل خطوة في المخطط."""
    timestamp: str
    node_id: str
    tool_name: str
    status: str  # SUCCESS, FAILED, FALLBACK, SKIPPED
    summary: str
    duration_seconds: float = 0.0


class ExecutionContext:
    """
    حاوية الحالة المركزية (Context / Blackboard Pattern).
    تسمح بتبادل البيانات والوسائط بين جميع وحدات التنفيذ الـ 18
    وتحفظ التاريخ التشغيلي وسجلات الأخطاء للتدقيق والتعافي الذاتي.
    """

    def __init__(self, goal: str = "", session_id: Optional[str] = None, initial_data: Optional[Dict[str, Any]] = None):
        self.session_id: str = session_id or str(uuid.uuid4())[:8]
        self.goal: str = goal
        self.created_at: str = datetime.datetime.now().isoformat()
        self.data: Dict[str, Any] = initial_data.copy() if initial_data else {}
        self.history: List[ExecutionRecord] = []
        self.errors: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """تخزين قيمة معينة في الحالة المشتركة."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """استرجاع قيمة من الحالة المشتركة مع دعم قيمة افتراضية."""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """التحقق من وجود مفتاح في الحالة."""
        return key in self.data

    def update(self, mapping: Dict[str, Any]) -> None:
        """تحديث قيم متعددة دفعة واحدة."""
        self.data.update(mapping)

    def log_step(
        self,
        node_id: str,
        tool_name: str,
        status: str,
        summary: str,
        duration_seconds: float = 0.0
    ) -> None:
        """توثيق نتيجة تنفيذ عقدة في سجل التاريخ."""
        record = ExecutionRecord(
            timestamp=datetime.datetime.now().isoformat(),
            node_id=node_id,
            tool_name=tool_name,
            status=status,
            summary=summary,
            duration_seconds=round(duration_seconds, 3)
        )
        self.history.append(record)

    def add_error(self, error: str) -> None:
        """إضافة رسالة خطأ إلى قائمة الأخطاء."""
        self.errors.append(error)

    def is_successful(self) -> bool:
        """هل تم التنفيذ دون أخطاء حرجة؟"""
        return len(self.errors) == 0

    def snapshot(self) -> Dict[str, Any]:
        """إرجاع لقطة كاملة للحالة قابلة للتسلسل (JSON-serializable)."""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "created_at": self.created_at,
            "data_keys": list(self.data.keys()),
            "errors": self.errors,
            "history_count": len(self.history),
            "records": [
                {
                    "node_id": r.node_id,
                    "tool": r.tool_name,
                    "status": r.status,
                    "summary": r.summary,
                    "duration": r.duration_seconds
                }
                for r in self.history
            ]
        }

    def summary(self) -> str:
        """عرض ملخص نصي أنيق للحالة التنفيذية."""
        lines = [
            f"=== Execution Context Summary [Session: {self.session_id}] ===",
            f"Goal: {self.goal or 'N/A'}",
            f"Active Keys: {', '.join(self.data.keys()) if self.data else 'None'}",
            f"Errors: {len(self.errors)}",
            f"Steps Executed: {len(self.history)}"
        ]
        for idx, rec in enumerate(self.history, 1):
            lines.append(f"  {idx}. [{rec.status}] Node '{rec.node_id}' ({rec.tool_name}): {rec.summary} ({rec.duration_seconds}s)")
        return "\n".join(lines)
