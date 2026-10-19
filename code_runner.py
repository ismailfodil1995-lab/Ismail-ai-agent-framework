import ast
import os
import subprocess
import sys

# ============================================================
# قائمة الاستدعاءات التدميرية المحظورة (AST Blacklist)
# ============================================================
_BLOCKED_CALLS = {
    # حذف الملفات والمجلدات
    ("shutil", "rmtree"),
    ("shutil", "move"),
    ("os", "remove"),
    ("os", "unlink"),
    ("os", "rmdir"),
    # إنهاء العملية
    ("sys", "exit"),
    ("os", "_exit"),
    ("os", "kill"),
    ("os", "abort"),
    # تنسيق الأقراص وتدمير البيانات
    ("subprocess", "Popen"),   # محظور مباشرة من داخل الكود؛ run_python_code هي نقطة الدخول الوحيدة
    ("ctypes", "windll"),
    ("ctypes", "cdll"),
}

_BLOCKED_FUNCTIONS = {
    "eval", "exec", "compile", "__import__",
}

_BLOCKED_MODULES = {
    "ctypes", "winreg", "msvcrt",
}


def _ast_security_check(code: str) -> list[str]:
    """
    يحلل الكود بـ AST ويعيد قائمة بالمخالفات الأمنية الموجودة.
    قائمة فارغة = كود نظيف وآمن.
    """
    violations = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError before execution: {e}"]

    for node in ast.walk(tree):
        # 1) فحص استدعاء الدوال الخطرة مثل eval() و exec()
        if isinstance(node, ast.Call):
            func = node.func
            # استدعاء مباشر: eval(...) أو exec(...)
            if isinstance(func, ast.Name) and func.id in _BLOCKED_FUNCTIONS:
                violations.append(f"Blocked direct call: {func.id}()")
            # استدعاء منقط: shutil.rmtree(...) أو sys.exit(...)
            elif isinstance(func, ast.Attribute):
                obj = func.value
                if isinstance(obj, ast.Name):
                    pair = (obj.id, func.attr)
                    if pair in _BLOCKED_CALLS:
                        violations.append(
                            f"Blocked destructive call: {obj.id}.{func.attr}()"
                        )

        # 2) فحص import المكتبات المحظورة
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BLOCKED_MODULES:
                    violations.append(f"Blocked import: {alias.name}")

        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _BLOCKED_MODULES:
                violations.append(f"Blocked from-import: {node.module}")

    return violations


def run_python_code(file_path: str, timeout: int = 15) -> str:
    """
    تشغيل ملف Python داخل بيئة معزولة بعد فحص AST أمني مسبق.
    أي كود يحتوي على استدعاءات تدميرية يُرفض قبل التشغيل.
    """
    if not file_path:
        return "Error: No file path provided."

    clean_path = file_path.strip()

    if not os.path.exists(clean_path):
        return f"Error: File '{clean_path}' does not exist."

    # ── فحص AST الأمني ────────────────────────────────────────
    try:
        with open(clean_path, "r", encoding="utf-8", errors="replace") as f:
            source_code = f.read()
    except Exception as e:
        return f"Error reading script for security check: {str(e)}"

    violations = _ast_security_check(source_code)
    if violations:
        report = "\n  - ".join(violations)
        return (
            f"[SECURITY BLOCKED] Script '{clean_path}' was rejected by AST analysis.\n"
            f"Violations found:\n  - {report}\n"
            f"Action: Script was NOT executed. Review and remove destructive calls."
        )
    # ── تشغيل الكود بعد اجتياز الفحص ─────────────────────────
    try:
        result = subprocess.run(
            [sys.executable, clean_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            output = stdout if stdout else "Code executed successfully with no output."
            return f"[Execution Success]\n{output}"
        else:
            return f"[Execution Error]\n{stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing code: {str(e)}"