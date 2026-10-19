"""
DAGEngine: محرك الرسوم البيانية الموجهة غير الدورية لإدارة تدفقات العمل الذاتية
"""
from typing import Dict, List, Optional, Set
from orchestrator.context import ExecutionContext
from orchestrator.node import TaskNode


class DAGEngine:
    """
    محرك تنفيذ الرسوم البيانية الموجهة (DAG Engine).
    يقوم بفحص صحة التبعيات، كشف الحلقات المفرغة (Cycle Detection)،
    وترتيب العقد طوبولوجياً (Topological Sorting) لضمان تسلسل العمليات دون أخطاء.
    """

    def __init__(self, context: Optional[ExecutionContext] = None):
        self.context: ExecutionContext = context or ExecutionContext()
        self.nodes: Dict[str, TaskNode] = {}

    def add_node(self, node: TaskNode) -> "DAGEngine":
        """إضافة عقدة تنفيذية إلى المخطط."""
        if node.node_id in self.nodes:
            raise ValueError(f"Node with ID '{node.node_id}' already exists in DAG.")
        self.nodes[node.node_id] = node
        return self

    def add_nodes(self, nodes: List[TaskNode]) -> "DAGEngine":
        """إضافة قائمة من العقد دفعة واحدة."""
        for node in nodes:
            self.add_node(node)
        return self

    def validate(self) -> List[str]:
        """
        التحقق من صحة المخطط وترتيب العقد طوبولوجياً باستخدام خوارزمية Kahn:
        - التحقق من وجود جميع التبعيات المذكورة.
        - كشف أي حلقات مغلقة (Cyclic Dependencies).
        ترجع قائمة بمعرفات العقد مرتبة حسب أولوية التنفيذ.
        """
        # 1. التحقق من سلامة التبعيات
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(
                        f"Unresolved dependency: Node '{node_id}' depends on non-existent node '{dep}'."
                    )

        # 2. حساب درجات الدخل (In-degree)
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        adj_list: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}

        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                adj_list[dep].append(node_id)
                in_degree[node_id] += 1

        # 3. طابور العقد التي لا تعتمد على شيء (In-degree = 0)
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        sorted_order: List[str] = []

        while queue:
            current = queue.pop(0)
            sorted_order.append(current)

            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 4. إذا لم يشمل الترتيب كل العقد، فهناك حلقة مفرغة
        if len(sorted_order) != len(self.nodes):
            unresolved = [nid for nid, deg in in_degree.items() if deg > 0]
            raise ValueError(f"Cyclic dependency detected involving nodes: {unresolved}")

        return sorted_order

    def run(self, context: Optional[ExecutionContext] = None, stop_on_failure: bool = True) -> ExecutionContext:
        """
        تشغيل المخطط بالكامل:
        - يفرز العقد بترتيب التبعيات.
        - ينفذ كل عقدة ويمرر الحالة المحدثة للعقد اللاحقة.
        - إذا فشلت عقدة حاسمة، يتوقف المسار أو يتجاوز الفروع التابعة لها بذكاء.
        """
        if context:
            self.context = context

        execution_order = self.validate()
        failed_nodes: Set[str] = set()

        for node_id in execution_order:
            node = self.nodes[node_id]

            # فحص إذا كانت أي من التبعيات قد فشلت مسبقاً
            has_failed_dependency = any(dep in failed_nodes for dep in node.dependencies)
            if has_failed_dependency:
                self.context.log_step(
                    node_id,
                    node.tool_key,
                    "SKIPPED",
                    f"Skipped because upstream dependency failed: {node.dependencies}"
                )
                failed_nodes.add(node_id)
                continue

            success = node.execute(self.context)

            if not success:
                failed_nodes.add(node_id)
                if stop_on_failure:
                    self.context.add_error(f"Workflow halted due to failure at node '{node_id}'.")
                    break

        return self.context

    def to_mermaid(self) -> str:
        """توليد مخطط تمثيلي للـ DAG بصيغة Mermaid."""
        lines = ["graph TD"]
        for node_id, node in self.nodes.items():
            clean_name = f"{node_id}['{node_id} ({node.tool_key})']"
            lines.append(f"    {clean_name}")
            for dep in node.dependencies:
                lines.append(f"    {dep} --> {node_id}")
        return "\n".join(lines)
