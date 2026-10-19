"""
TaskNode: مغلف العقدة الذكية لربط وتكامل الأدوات الحالية بنمط الـ Adapter
"""
import time
from typing import Any, Callable, Dict, List, Optional
from orchestrator.context import ExecutionContext

def _get_available_tools() -> Dict[str, Any]:
    """استرجاع ديناميكي لقاموس الأدوات لتفادي الاستيراد الدائري"""
    try:
        from brain import AVAILABLE_TOOLS
        if AVAILABLE_TOOLS:
            return AVAILABLE_TOOLS
    except Exception:
        pass
    try:
        from tools import AVAILABLE_TOOLS
        return AVAILABLE_TOOLS
    except Exception:
        return {}


from services.guardrails import guardrails
from services.reflection_engine import reflection_engine


class TaskNode:
    """
    عقدة تنفيذية ذكية داخل شبكة الـ DAG.
    تلف الأدوات الـ 18 الحالية بنمط الـ Adapter دون أي تعديل في كودها،
    مع توفير دعم الشروط المنطقية، التحقق، إعادة المحاولة، والتعافي التلقائي.
    """

    def __init__(
        self,
        node_id: str,
        tool_key: str,
        input_mapping: Optional[Dict[str, Any]] = None,
        output_key: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        fallback_tool_key: Optional[str] = None,
        fallback_input_mapping: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[ExecutionContext], bool]] = None,
        validator: Optional[Callable[[Any], bool]] = None,
        retries: int = 2,
        retry_delay: float = 0.3,
        description: str = ""
    ):
        self.node_id: str = node_id
        self.tool_key: str = tool_key
        self.input_mapping: Dict[str, Any] = input_mapping or {}
        self.output_key: Optional[str] = output_key
        self.dependencies: List[str] = dependencies or []
        self.fallback_tool_key: Optional[str] = fallback_tool_key
        self.fallback_input_mapping: Dict[str, Any] = fallback_input_mapping or self.input_mapping
        self.condition: Optional[Callable[[ExecutionContext], bool]] = condition
        self.validator: Optional[Callable[[Any], bool]] = validator
        self.retries: int = max(1, retries)
        self.retry_delay: float = retry_delay
        self.description: str = description

    def _resolve_inputs(self, mapping: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        استخراج وحل مدخلات الأداة ديناميكياً من سياق الحالة:
        - إذا بدأت القيمة بـ 'context:' أو '$'، يتم جلبها من context.data.
        - إذا كانت القيمة دالة قابلة للاستدعاء Callable، يتم تمرير context لها.
        - عدا ذلك، تُعتبر قيمة ثابتة.
        """
        resolved = {}
        for param_name, src in mapping.items():
            if callable(src):
                resolved[param_name] = src(context)
            elif isinstance(src, str) and (src.startswith("context:") or src.startswith("$")):
                raw_key = src.split(":", 1)[-1] if src.startswith("context:") else src[1:]
                resolved[param_name] = context.get(raw_key)
            else:
                resolved[param_name] = src
        return resolved

    def _default_validator(self, result: Any) -> bool:
        """فحص افتراضي لجودة مخرجات الأداة."""
        if result is None:
            return False
        if isinstance(result, str):
            res_clean = result.strip().lower()
            if res_clean.startswith("error") or res_clean.startswith("exception"):
                return False
        return True

    def execute(self, context: ExecutionContext) -> bool:
        """
        تنفيذ العقدة:
        1. التحقق من الشرط المنطقي إن وجد.
        2. حل المدخلات من الـ Context.
        3. استدعاء الأداة مع دعم الـ Retries.
        4. تفعيل خطة التعافي التلقائي (Fallback) عند الضرورة.
        """
        start_time = time.time()

        # 1. فحص شرط التفرع المنطقي
        if self.condition is not None:
            try:
                should_run = self.condition(context)
                if not should_run:
                    duration = time.time() - start_time
                    context.log_step(self.node_id, self.tool_key, "SKIPPED", "Condition evaluated to False", duration)
                    return True
            except Exception as cond_err:
                context.add_error(f"Node '{self.node_id}' condition evaluation failed: {cond_err}")
                return False

        # 2. التحقق من وجود الأداة في القاموس المعتمد
        available_tools = _get_available_tools()
        if self.tool_key not in available_tools:
            context.add_error(f"Node '{self.node_id}': Tool '{self.tool_key}' not found in AVAILABLE_TOOLS.")
            context.log_step(self.node_id, self.tool_key, "FAILED", "Tool not registered", time.time() - start_time)
            return False

        tool_meta = available_tools[self.tool_key]
        fn = tool_meta.get("fn") or tool_meta.get("function")
        if not callable(fn):
            context.add_error(f"Node '{self.node_id}': Target '{self.tool_key}' has no callable function.")
            return False

        resolved_inputs = self._resolve_inputs(self.input_mapping, context)
        validator_func = self.validator or self._default_validator

        # 3. فحص بوابة الحوكمة والأمان للأدوات الحساسة
        allowed, guard_msg = guardrails.verify_action(
            self.tool_key,
            resolved_inputs,
            context_description=f"DAG Node '{self.node_id}': {self.description or self.tool_key}"
        )
        if not allowed:
            duration = time.time() - start_time
            context.add_error(f"Node '{self.node_id}' blocked by guardrail: {guard_msg}")
            context.log_step(self.node_id, self.tool_key, "BLOCKED", guard_msg, duration)
            return False

        last_error = ""

        # 4. دورة التنفيذ والتصحيح الذاتي (Execution & Self-Healing Loop)
        for attempt in range(1, self.retries + 1):
            try:
                result = fn(**resolved_inputs)
                if validator_func(result):
                    if self.output_key:
                        context.set(self.output_key, result)
                    duration = time.time() - start_time
                    summary = f"Success (attempt {attempt}): " + str(result)[:60].replace("\n", " ")
                    context.log_step(self.node_id, self.tool_key, "SUCCESS", summary, duration)
                    return True
                else:
                    last_error = f"Output validation failed on attempt {attempt}: {str(result)[:80]}"
            except Exception as e:
                last_error = f"Execution exception on attempt {attempt}: {str(e)}"

            # محاولة التصحيح الذاتي قبل استئناف المحاولة التالية
            if attempt < self.retries:
                fixed, corrected_inputs, reason = reflection_engine.reflect_and_correct(
                    self.tool_key,
                    resolved_inputs,
                    last_error,
                    context_hint=f"Node '{self.node_id}': {self.description}"
                )
                if fixed and corrected_inputs != resolved_inputs:
                    resolved_inputs = corrected_inputs
                time.sleep(self.retry_delay)

        # 5. محاولة التعافي التلقائي بالأداة البديلة (Fallback Recovery)
        if self.fallback_tool_key and self.fallback_tool_key in AVAILABLE_TOOLS:
            try:
                fallback_meta = AVAILABLE_TOOLS[self.fallback_tool_key]
                fallback_fn = fallback_meta.get("fn") or fallback_meta.get("function")
                fallback_inputs = self._resolve_inputs(self.fallback_input_mapping, context)
                fallback_res = fallback_fn(**fallback_inputs)
                if validator_func(fallback_res):
                    if self.output_key:
                        context.set(self.output_key, fallback_res)
                    duration = time.time() - start_time
                    context.log_step(
                        self.node_id,
                        f"{self.tool_key}->{self.fallback_tool_key}",
                        "FALLBACK_SUCCESS",
                        f"Recovered via fallback: {str(fallback_res)[:60]}",
                        duration
                    )
                    return True
            except Exception as fb_err:
                last_error += f" | Fallback failed: {str(fb_err)}"

        # فشل العقدة بعد استنفاد كل المحاولات والبدائل
        duration = time.time() - start_time
        context.add_error(f"Node '{self.node_id}' failed: {last_error}")
        context.log_step(self.node_id, self.tool_key, "FAILED", last_error, duration)
        return False
