from typing import Any, Dict, List, Optional
from tools import register_tool
from services.tool_registry_bridge import tool_bridge


@register_tool(
    name="compile_dag_workflow",
    description="تحويل الأهداف المعقدة باللغة الطبيعية إلى مسار عمل DAG ديناميكي وتنفيذه."
)
def compile_dag_workflow(
    goal: str = "",
    initial_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    تجميع خطة مهام ذاتية وتحويلها إلى شبكة رسم بياني موجه (DAG) وتنفيذها عبر DAGEngine.
    """
    for k in ["prompt", "task", "objective", "plan_text"]:
        if k in kwargs and kwargs[k]:
            goal = kwargs[k]
            break

    for k in ["data", "context", "inputs"]:
        if k in kwargs and kwargs[k]:
            initial_data = kwargs[k]
            break

    if not goal or not str(goal).strip():
        return "Error: No goal provided to compile DAG workflow."

    from orchestrator.context import ExecutionContext
    from orchestrator.node import TaskNode
    from orchestrator.dag_engine import DAGEngine

    ctx = ExecutionContext(goal=goal, initial_data=initial_data or {})
    engine = DAGEngine(ctx)

    try:
        # 1. تحليل الهدف عبر الـ Planner لاستخراج خطوات التنفيذ
        from planner import planner
        plan = planner.make_plan(goal)
        nodes: List[TaskNode] = []

        if isinstance(plan, dict) and plan.get("type") == "plan" and plan.get("steps"):
            steps = plan.get("steps", [])
            prev_node_id: Optional[str] = None

            for idx, step in enumerate(steps, start=1):
                tool_name = step.get("tool", "")
                args = step.get("args", {})
                node_id = f"step_{idx}_{tool_name}"

                # التحقق من أن الأداة مسجلة في النظام
                if not tool_bridge.has_tool(tool_name):
                    matched = tool_bridge.match_tool_name(tool_name)
                    tool_name = matched if matched else tool_name

                deps = [prev_node_id] if prev_node_id else []
                node = TaskNode(
                    node_id=node_id,
                    tool_key=tool_name,
                    input_mapping=args,
                    output_key=f"output_{node_id}",
                    dependencies=deps,
                    description=f"Auto-generated step {idx}: {tool_name}"
                )
                nodes.append(node)
                prev_node_id = node_id

        # 2. إذا لم يكن مخططاً متعدد الخطوات، ننشئ عقدة واحدة للطلب
        elif isinstance(plan, dict) and plan.get("type") == "tool":
            tool_name = plan.get("tool", "")
            args = plan.get("args", {})
            nodes.append(
                TaskNode(
                    node_id="single_step",
                    tool_key=tool_name,
                    input_mapping=args,
                    output_key="result",
                    description=f"Direct action: {tool_name}"
                )
            )

        # 3. خطة احتياطية قياسية إذا لم ترجع خطة واضحة
        else:
            nodes.append(
                TaskNode(
                    node_id="qualify_step",
                    tool_key="qualify_lead",
                    input_mapping={"client_info": goal},
                    output_key="lead_report",
                    description="Analyze and qualify input requirement"
                )
            )

        engine.add_nodes(nodes)
        result_ctx = engine.run()

        status = "SUCCESS" if result_ctx.is_successful() else "COMPLETED_WITH_ERRORS"
        return f"{status}: Dynamic DAG Workflow executed for goal '{goal}':\n\n{result_ctx.summary()}"

    except Exception as e:
        return f"Error compiling and executing DAG workflow: {str(e)}"


@register_tool(
    name="execute_dag_template",
    description="تشغيل مسار عمل DAG جاهز عبر معرف القالب (template_id) مثل lead_enrichment أو duckdb_analytics."
)
def execute_dag_template(
    template_id: str = "",
    inputs: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    استدعاء مسار عمل DAG مسبق الإعداد من WORKFLOW_TEMPLATES وتنفيذه فوراً.
    """
    for k in ["id", "workflow_id", "template", "name"]:
        if k in kwargs and kwargs[k]:
            template_id = kwargs[k]
            break

    for k in ["args", "parameters", "data"]:
        if k in kwargs and kwargs[k]:
            inputs = kwargs[k]
            break

    if not template_id:
        return "Error: No 'template_id' provided to execute_dag_template."

    combined_inputs = dict(inputs or {})
    for k, v in kwargs.items():
        if k not in ["template_id", "inputs", "id", "workflow_id", "template", "name", "args", "parameters", "data"]:
            combined_inputs[k] = v

    try:
        from orchestrator.templates import instantiate_workflow
        engine = instantiate_workflow(template_id, **combined_inputs)
        ctx = engine.run()
        status = "SUCCESS" if ctx.is_successful() else "COMPLETED_WITH_ERRORS"
        return f"{status}: Executed DAG Template '{template_id}':\n\n{ctx.summary()}"

    except Exception as e:
        return f"Error executing DAG template '{template_id}': {str(e)}"
