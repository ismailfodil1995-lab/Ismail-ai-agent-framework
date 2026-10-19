"""
test_system_improvements.py
اختبار متكامل للتحسينات المنفذة:
  1. اختبار الـ Planner (إلغاء Hardcoded، ديناميكية LLM، و Sparse Tool Loading)
  2. اختبار الـ Executor (الـ Structured Logging وتتبع مطابقة الأدوات والمدخلات والمخرجات)
  3. اختبار نقطة /health المطورة (فحص صحة المحركات، سلامة الأدوات، والبيئة)
"""
import asyncio
import logging
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ضبط الـ Logger لاختبار ومراقبة الـ Structured Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("test_suite")


def test_planner_sparse_and_dynamic():
    print("\n" + "=" * 60)
    print("🔹 [1/3] اختبار الـ Planner & Sparse Tool Loading")
    print("=" * 60)

    from planner import planner, TOOL_CATEGORIES, _build_sparse_tool_prompt

    # 1. التأكد من تغطية الفئات الشاملة
    assert len(TOOL_CATEGORIES) >= 7, f"Expected at least 7 categories, got {len(TOOL_CATEGORIES)}"
    print(f"✅ فئات الأدوات المعرفة للـ Sparse Loading: {list(TOOL_CATEGORIES.keys())}")

    # 2. اختبار بناء موجه Sparse Tools لمجموعة محددة
    sparse_text, loaded = _build_sparse_tool_prompt(["data"])
    print(f"✅ تم تحميل أدوات فئة 'data' فقط: {loaded}")
    assert "query_duckdb" in loaded
    assert "search_web" not in loaded  # تأكيد عدم تحميل أدوات الويب لمنع Token Overflow
    assert len(sparse_text) > 50

    # 3. اختبار التخطيط وتوليد الخطة بالـ LLM
    test_query = "اقرأ ملف البيانات واستخرج المتوسط"
    print(f"--> اختبار استدعاء make_plan للطلب: '{test_query}'")
    plan = planner.make_plan(test_query)
    print(f"نتيجة الخطة: {plan}")
    assert isinstance(plan, dict)
    assert "type" in plan
    print("✅ نجح التخطيط الديناميكي بالـ LLM بنجاح تام.")


def test_executor_structured_logging():
    print("\n" + "=" * 60)
    print("🔹 [2/3] اختبار الـ Executor & Structured Logging")
    print("=" * 60)

    from executor import executor

    # 1. فحص طريقة مطابقة الأوامر المهيكلة وتوثيقها في الـ Logs
    cmd_dict = {"tool": "write_system_file", "args": {"filename": "health_temp.txt", "content": "OK"}}
    tool, args = executor._resolve_tool_and_args(cmd_dict)
    assert tool == "write_system_file"
    assert args.get("filename") == "health_temp.txt"
    print(f"✅ مطابقة أمر مهيكل (structured_dict): {tool} -> {args}")

    # 2. تنفيذ الأمر وملاحظة الـ Structured Logs
    res = executor.execute([cmd_dict])
    print(f"✅ نتيجة التنفيذ: {res}")
    assert os.path.exists("health_temp.txt")

    # 3. قراءة الملف عبر Executor
    read_cmd = {"tool": "read_system_file", "args": {"filename": "health_temp.txt"}}
    read_res = executor.execute([read_cmd])
    print(f"✅ نتيجة القراءة: {read_res}")
    assert "OK" in read_res

    # تنظيف الملف المؤقت
    if os.path.exists("health_temp.txt"):
        os.remove("health_temp.txt")


def test_health_endpoint():
    print("\n" + "=" * 60)
    print("🔹 [3/3] اختبار نقطة /health المطورة وفحص المحركات والأدوات")
    print("=" * 60)

    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed with {response.status_code}"

    data = response.json()
    print("تقرير فحص الصحة الكامل المستخرج من /health:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # التحقق من البيانات المسترجعة
    assert data["status"] in ["healthy", "degraded"]
    assert data["tools_count"] >= 20
    assert "engines" in data
    assert "tools_health" in data
    assert "environment" in data

    # التأكد من فحص المحركات
    engines = data["engines"]
    assert "planner" in engines and engines["planner"]["status"] == "ready"
    assert "executor" in engines and engines["executor"]["status"] == "ready"
    assert "guardrails" in engines
    assert "reflection" in engines
    assert "orchestrator" in engines

    # التأكد من سلامة الأدوات
    tools_health = data["tools_health"]
    assert tools_health["total_registered"] == data["tools_count"]
    assert len(tools_health["unhealthy_tools"]) == 0
    print("\n✅ جميع المحركات (Engines) والأدوات (Tools) جاهزة وتعمل بكفاءة 100%!")


if __name__ == "__main__":
    test_planner_sparse_and_dynamic()
    test_executor_structured_logging()
    test_health_endpoint()
    print("\n" + "=" * 60)
    print("🎉 تم اجتياز جميع اختبارات التحسينات بنجاح تام!")
    print("=" * 60)
