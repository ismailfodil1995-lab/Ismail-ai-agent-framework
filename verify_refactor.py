"""
verify_refactor.py
سكريبت التحقق من نجاح التفكيك المعماري وتأمين AST
"""
import sys, os

print("=" * 60)
print("REFACTOR VERIFICATION")
print("=" * 60)

# 1. فحص تحميل tools/__init__.py والأدوات الأربعة الجديدة
from tools import AVAILABLE_TOOLS
print(f"[1] AVAILABLE_TOOLS count: {len(AVAILABLE_TOOLS)}")

expected_new = [
    "generate_excel_report", "read_excel_file",
    "schedule_task",
    "list_system_files", "read_system_file",
    "write_system_file", "run_system_code",
    "open_browser_url", "browser_search",
]
for t in expected_new:
    status = "OK" if t in AVAILABLE_TOOLS else "MISSING"
    print(f"    [{status}] {t}")

# 2. فحص AST Security في code_runner.py
print()
print("[2] AST Security check:")
from code_runner import _ast_security_check

safe_code = "print('hello')\nimport os\nprint(os.getcwd())"
danger_code = "import shutil\nshutil.rmtree('/')"
eval_code = "eval('2+2')"

viol_safe   = _ast_security_check(safe_code)
viol_danger = _ast_security_check(danger_code)
viol_eval   = _ast_security_check(eval_code)

print(f"    Safe code violations   : {viol_safe}  (expected: [])")
print(f"    Danger code violations : {viol_danger}")
print(f"    eval() code violations : {viol_eval}")
ast_pass = (not viol_safe) and bool(viol_danger) and bool(viol_eval)
print("    AST BLOCK TEST:", "PASS" if ast_pass else "FAIL")

# 3. فحص نظافة brain.py
print()
print("[3] brain.py purity check:")
with open("brain.py", "r", encoding="utf-8") as f:
    content = f.read()

has_inline_schedule = "def schedule_task" in content
has_inline_excel    = "def generate_excel_report" in content
has_webbrowser_open = "webbrowser.open" in content

print(f"    def schedule_task in brain.py       : {has_inline_schedule}  (expected: False)")
print(f"    def generate_excel_report in brain.py: {has_inline_excel}  (expected: False)")
print(f"    webbrowser.open in brain.py          : {has_webbrowser_open}  (expected: False)")

purity_pass = not has_inline_schedule and not has_inline_excel and not has_webbrowser_open
print("    BRAIN PURITY:", "PASS" if purity_pass else "FAIL")

# 4. ملخص
print()
print("=" * 60)
all_ok = ast_pass and purity_pass and "MISSING" not in "".join(
    "MISSING" if t not in AVAILABLE_TOOLS else "" for t in expected_new
)
print("FINAL RESULT:", "ALL CHECKS PASSED [OK]" if all_ok else "SOME CHECKS FAILED [!!]")
print("=" * 60)
