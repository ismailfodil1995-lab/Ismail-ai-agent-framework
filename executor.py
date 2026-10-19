"""
executor.py - محرك التنفيذ المتطور (Async & Parallel Executor with Structured Logging)
=====================================================================================
الميزات الأساسية:
  1. البرمجة غير المتزامنة (async/await) والمعالجة المتوازية عبر asyncio.gather.
  2. التوافق الكامل مع الاستدعاءات المتزامنة (Sync Fallback).
  3. بوابات الحوكمة والأمان (Guardrails) وحلقة التصحيح الذاتي (Self-Healing Reflection Loop).
  4. Structured Logging شامل: يوثق طريقة مطابقة الأداة، المدخلات، المخرجات، زمن التنفيذ، وحالات التصحيح الذاتي.
"""
import asyncio
import inspect
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from brain import AVAILABLE_TOOLS
except ImportError:
    from tools import AVAILABLE_TOOLS

from services.tool_registry_bridge import tool_bridge
from services.guardrails import guardrails
from services.reflection_engine import reflection_engine
from config import MAX_REFLECTION_ATTEMPTS

logger = logging.getLogger("ai_agent.executor")


class Executor:
    """
    محرك التنفيذ المتطور:
    - يدعم البرمجة غير المتزامنة (async/await)
    - يدعم المعالجة المتوازية للمهام المستقلة عبر asyncio.gather
    - يحافظ على التوافق الكامل مع الاستدعاءات المتزامنة (Sync Fallback)
    - مزود ببوابات الحوكمة والأمان (Guardrails) وحلقة التصحيح الذاتي (Self-Healing Reflection Loop)
    - مدعوم بسجلات تتبع مهيكلة (Structured Logging) لكل العمليات.
    """

    def __init__(self, max_retries: int = MAX_REFLECTION_ATTEMPTS):
        self.max_retries = max_retries

    def parse_commands(self, user_input: Union[str, List[Any]]) -> List[Any]:
        """تقسيم الأوامر المركبة بناءً على أدوات الربط أو استخراج قائمة المهام المهيكلة"""
        if not user_input:
            return []

        if isinstance(user_input, list):
            return user_input

        pattern = r"\s+(?:and|then|then open|ثم|و|بعد ذلك)\s+|[,\n;]"
        raw_commands = re.split(pattern, str(user_input), flags=re.IGNORECASE)
        return [cmd.strip().strip("\"'") for cmd in raw_commands if cmd.strip()]

    def _resolve_tool_and_args(self, command: Any) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        استخراج اسم الأداة والوسائط سواء كانت مهيكلة كـ dict أو نصية،
        مع توثيق دقيق لطريقة المطابقة (Resolution Method) في الـ Structured Logs.
        """
        method = "unresolved"
        tool_name = None
        args: Dict[str, Any] = {}

        if isinstance(command, dict):
            tool_name = command.get("tool") or command.get("name")
            args = command.get("args", {})
            method = "structured_dict"
            logger.info(
                "[Executor][Resolve] method='%s' | tool='%s' | args=%s | raw_command='%s'",
                method, tool_name, args, str(command)[:100]
            )
            return tool_name, args

        cmd_str = str(command).strip()

        # 1. مطابقة مباشرة لاسم الأداة في AVAILABLE_TOOLS
        if cmd_str in AVAILABLE_TOOLS:
            tool_name = cmd_str
            method = "exact_match"

        # 2. البحث عن اسم أداة يبدأ به الأمر مع استخراج المعامل اللاحق
        if not tool_name:
            for candidate in AVAILABLE_TOOLS:
                if cmd_str.startswith(candidate):
                    tool_name = candidate
                    method = "prefix_match"
                    arg_val = cmd_str[len(candidate):].strip()
                    if arg_val:
                        try:
                            meta = tool_bridge.get_all_tools_metadata().get(candidate, {})
                            props = list(meta.get("parameters", {}).get("properties", {}).keys())
                            if props:
                                args[props[0]] = arg_val
                        except Exception:
                            pass
                    break

        # 3. مطابقة اسم أداة داخل جملة الأمر
        if not tool_name:
            for candidate in AVAILABLE_TOOLS:
                if candidate in cmd_str:
                    tool_name = candidate
                    method = "substring_match"
                    break

        # 4. مطابقة ذكية عبر tool_bridge
        if not tool_name:
            try:
                matched = tool_bridge.match_tool_name(cmd_str)
                if matched:
                    tool_name = matched
                    method = "bridge_match"
            except Exception:
                pass

        logger.info(
            "[Executor][Resolve] method='%s' | tool='%s' | args=%s | raw_command='%s'",
            method, tool_name, args, cmd_str[:100]
        )
        return tool_name, args

    async def _execute_tool_with_retry_async(self, tool_command: Any) -> str:
        """
        تنفيذ غير متزامن للأداة مع فحص بوابات الأمان والتصحيح الذاتي في بيئة غير حاجزة (Non-blocking)
        مع تسجيل Structured Logging في كل خطوة.
        """
        tool_name, initial_args = self._resolve_tool_and_args(tool_command)
        current_args = dict(initial_args)

        # Fallback إلى tool_manager إن لم توجد الأداة في AVAILABLE_TOOLS
        if not tool_name or tool_name not in AVAILABLE_TOOLS:
            try:
                from tool_manager import tool_manager
                logger.info(
                    "[Executor][Fallback] tool='%s' not in AVAILABLE_TOOLS, delegating to tool_manager",
                    tool_command
                )
                result = await asyncio.to_thread(tool_manager.execute, str(tool_command))
                if result is not None:
                    return str(result)
            except Exception as e:
                logger.warning("[Executor][Fallback] tool_manager execution failed: %s", e)
            return f"Tool '{tool_command}' not recognized in available framework skills."

        # 1. بوابة الحوكمة والأمان
        allowed, security_msg = guardrails.verify_action(
            tool_name,
            current_args,
            context_description=f"Executing: {tool_command}"
        )
        logger.info(
            "[Executor][Guardrail] tool='%s' | allowed=%s | reason='%s'",
            tool_name, allowed, security_msg
        )
        if not allowed:
            logger.warning(
                "[Executor][GuardrailBlocked] tool='%s' | args=%s | msg='%s'",
                tool_name, current_args, security_msg
            )
            return f"[SECURITY GUARDRAIL BLOCKED]: {security_msg}"

        tool_entry = AVAILABLE_TOOLS[tool_name]
        fn = tool_entry.get("fn") or tool_entry.get("function")
        if not fn:
            err_msg = f"Error: Tool '{tool_name}' has no executable function."
            logger.error("[Executor][ConfigError] %s", err_msg)
            return err_msg

        # 2. حلقة التنفيذ غير المتزامنة مع التصحيح الذاتي
        attempts = 0
        last_error = ""

        while attempts <= self.max_retries:
            attempts += 1
            t_exec_start = time.perf_counter()
            is_async_fn = inspect.iscoroutinefunction(fn) or asyncio.iscoroutinefunction(fn)

            logger.info(
                "[Executor][ExecuteStart] tool='%s' | attempt=%d/%d | is_async=%s | inputs=%s",
                tool_name, attempts, self.max_retries + 1, is_async_fn, current_args
            )

            try:
                # دعم الدوال المتزامنة وغير المتزامنة
                if is_async_fn:
                    try:
                        res = await (fn(**current_args) if current_args else fn())
                    except TypeError:
                        res = await fn()
                else:
                    # تشغيل الدوال المتزامنة داخل Thread Pool لعدم تجميد الـ Event Loop
                    try:
                        if current_args:
                            res = await asyncio.to_thread(fn, **current_args)
                        else:
                            res = await asyncio.to_thread(fn)
                    except TypeError:
                        res = await asyncio.to_thread(fn)

                elapsed_ms = round((time.perf_counter() - t_exec_start) * 1000, 1)
                res_str = str(res) if res is not None else ""

                if res_str.lower().startswith("error:"):
                    last_error = res_str
                    logger.warning(
                        "[Executor][ExecuteError] tool='%s' | attempt=%d/%d | error='%s' | elapsed_ms=%.1f",
                        tool_name, attempts, self.max_retries + 1, last_error, elapsed_ms
                    )
                    if attempts <= self.max_retries:
                        fixed, corrected_args, reason = reflection_engine.reflect_and_correct(
                            tool_name,
                            current_args,
                            last_error,
                            context_hint=str(tool_command)
                        )
                        if fixed and corrected_args != current_args:
                            logger.info(
                                "[Executor][SelfHealing] tool='%s' | reason='%s' | corrected_args=%s",
                                tool_name, reason, corrected_args
                            )
                            print(f"[Self-Healing] {reason} -> Retrying with corrected args: {corrected_args}")
                            current_args = corrected_args
                            await asyncio.sleep(0.2)
                            continue
                    return res_str

                final_output = res_str if res_str else "Executed successfully."
                logger.info(
                    "[Executor][ExecuteSuccess] tool='%s' | duration_ms=%.1f | output_snippet='%s'",
                    tool_name, elapsed_ms, final_output[:150].replace("\n", " ")
                )
                return final_output

            except Exception as error:
                elapsed_ms = round((time.perf_counter() - t_exec_start) * 1000, 1)
                last_error = str(error)
                logger.warning(
                    "[Executor][ExecuteException] tool='%s' | attempt=%d/%d | exception='%s' | elapsed_ms=%.1f",
                    tool_name, attempts, self.max_retries + 1, last_error, elapsed_ms
                )
                if attempts <= self.max_retries:
                    fixed, corrected_args, reason = reflection_engine.reflect_and_correct(
                        tool_name,
                        current_args,
                        last_error,
                        context_hint=str(tool_command)
                    )
                    if fixed and corrected_args != current_args:
                        logger.info(
                            "[Executor][SelfHealing] tool='%s' | reason='%s' | corrected_args=%s",
                            tool_name, reason, corrected_args
                        )
                        print(f"[Self-Healing] {reason} -> Retrying with corrected args: {corrected_args}")
                        current_args = corrected_args
                        await asyncio.sleep(0.2)
                        continue

                return f"Error executing '{tool_name}': {last_error}"

        timeout_msg = f"Tool '{tool_name}' returned error after {self.max_retries} attempts: {last_error}"
        logger.error("[Executor][ExecuteFailed] %s", timeout_msg)
        return timeout_msg

    def _execute_tool_with_retry(self, tool_command: Any) -> str:
        """نسخة متزامنة للتنفيذ المباشر (التوافق مع الإصدارات السابقة)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self._execute_tool_with_retry_async(tool_command))
                    return future.result()
            else:
                return loop.run_until_complete(self._execute_tool_with_retry_async(tool_command))
        except RuntimeError:
            return asyncio.run(self._execute_tool_with_retry_async(tool_command))

    async def execute_async(self, user_input: Any, parallel: bool = True) -> str:
        """
        دالة التنفيذ غير المتزامنة الأساسية:
        - عند تفعيل parallel=True ووجود عدة مهام، يتم تشغيلها بالتوازي عبر asyncio.gather
        - عند parallel=False، يتم التنفيذ تسلسلياً (Sequential)
        - توفر Structured Logging كامل لعمليات المعالجة المجمعة.
        """
        commands = self.parse_commands(user_input)
        if not commands:
            logger.info("[Executor][Batch] No valid commands found in input.")
            return "No valid commands found."

        t_batch_start = time.perf_counter()
        logger.info(
            "[Executor][BatchStart] total_commands=%d | parallel=%s",
            len(commands), parallel
        )

        if parallel and len(commands) > 1:
            print(f"[Async Parallel] Executing {len(commands)} tasks concurrently using asyncio.gather...")
            tasks = [self._execute_tool_with_retry_async(cmd) for cmd in commands]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            formatted_results = []
            for index, res in enumerate(raw_results, start=1):
                cmd_item = commands[index - 1]
                cmd_display = cmd_item if isinstance(cmd_item, str) else cmd_item.get("tool", str(cmd_item))
                if isinstance(res, Exception):
                    err_msg = f"Step {index} ({cmd_display}): Error - {str(res)}"
                    print(f"Agent [Parallel]: {err_msg}")
                    formatted_results.append(err_msg)
                else:
                    msg = f"Step {index} ({cmd_display}): {res if res else 'Executed.'}"
                    print(f"Agent [Parallel]: {msg}")
                    formatted_results.append(msg)

            batch_elapsed = round((time.perf_counter() - t_batch_start) * 1000, 1)
            logger.info(
                "[Executor][BatchComplete] parallel=True | total_commands=%d | elapsed_ms=%.1f",
                len(commands), batch_elapsed
            )
            return "\n".join(formatted_results)

        # تنفيذ تسلسلي غير متزامن
        results = []
        for index, cmd in enumerate(commands, start=1):
            cmd_display = cmd if isinstance(cmd, str) else cmd.get("tool", str(cmd))
            print(f"--> [Step {index}/{len(commands)}] Executing: '{cmd_display}'")
            res = await self._execute_tool_with_retry_async(cmd)
            if res:
                print(f"Agent: {res}")
                results.append(f"Step {index}: {res}")
            else:
                results.append(f"Step {index}: Executed.")

        batch_elapsed = round((time.perf_counter() - t_batch_start) * 1000, 1)
        logger.info(
            "[Executor][BatchComplete] parallel=False | total_commands=%d | elapsed_ms=%.1f",
            len(commands), batch_elapsed
        )
        return "\n".join(results)

    async def execute_parallel(self, user_input: Any) -> str:
        """تشغيل الأوامر بالتوازي الإجباري عبر asyncio.gather"""
        return await self.execute_async(user_input, parallel=True)

    def execute(self, user_input: Any, parallel: bool = False) -> str:
        """
        دالة التنفيذ المتزامنة الرئيسية للتوافقية الكاملة (Backwards-Compatible Sync Wrapper).
        تستخدم حلقة الأحداث (Event Loop) لإدارة التنفيذ.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self.execute_async(user_input, parallel=parallel))
                    return future.result()
            else:
                return loop.run_until_complete(self.execute_async(user_input, parallel=parallel))
        except RuntimeError:
            return asyncio.run(self.execute_async(user_input, parallel=parallel))


# Singleton Instance
executor = Executor()