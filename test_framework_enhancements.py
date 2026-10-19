"""
Test Suite: التحقق الشامل من ترقيات الـ Framework (المرحلة الأولى)
"""
import sys
import os

# ضبط ترميز UTF-8 للمخرجات لتجنب أخطاء CP1256 على Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from services.tool_registry_bridge import tool_bridge
from services.guardrails import guardrails, GuardrailsGateway
from services.reflection_engine import reflection_engine
from executor import executor
from orchestrator.context import ExecutionContext
from orchestrator.node import TaskNode
from orchestrator.dag_engine import DAGEngine


def test_schema_bridge():
    print("\n--- [1/5] اختبار جسر سجل الأدوات (Schema Bridge) ---")
    meta = tool_bridge.get_all_tools_metadata()
    print(f"✅ عدد الأدوات المستخرجة بالمخطط: {len(meta)} أداة.")
    assert len(meta) >= 18, f"Expected at least 18 tools, got {len(meta)}"

    # فحص بارامترات بعض الأدوات
    assert "write_system_file" in meta
    req = meta["write_system_file"]["parameters"].get("required", [])
    assert "filename" in req and "content" in req, f"Required fields missing: {req}"

    prompt_desc = tool_bridge.build_tool_prompt_description()
    assert len(prompt_desc) > 200
    print("✅ تم استخراج نصوص موجهات الأدوات بنجاح.")

    # التحقق من دالة فحص المدخلات
    valid, _ = tool_bridge.validate_tool_args("write_system_file", {"filename": "test.txt", "content": "hi"})
    assert valid is True
    invalid, msg = tool_bridge.validate_tool_args("write_system_file", {"filename": "test.txt"})
    assert invalid is False
    print("✅ تم التحقق من صحة واكتمال المعاملات بنجاح.")


def test_guardrails():
    print("\n--- [2/5] اختبار بوابة الحوكمة والأمان (Guardrails Gateway) ---")
    assert guardrails.is_critical("run_system_code") is True
    assert guardrails.is_critical("read_system_file") is False

    # 1. اختبار نمط auto (تلقائي مع توثيق)
    gw_auto = GuardrailsGateway(mode="auto")
    allowed, msg = gw_auto.verify_action("run_system_code", {"file_path": "dummy.py"})
    assert allowed is True
    assert len(gw_auto.get_audit_trail()) == 1
    print("✅ نمط Auto يسمح بالإجراء ويوثقه في سجل التدقيق الأمني.")

    # 2. اختبار نمط strict (حظر تام للعمليات الحرجة)
    gw_strict = GuardrailsGateway(mode="strict")
    allowed, msg = gw_strict.verify_action("run_system_code", {"file_path": "dummy.py"})
    assert allowed is False
    assert "blocked by strict policy" in msg.lower()
    print("✅ نمط Strict يحظر الإجراءات الحرجة بحزم.")

    # 3. اختبار دالة الموافقة المخصصة (Custom Approver)
    gw_custom = GuardrailsGateway(mode="ask")
    gw_custom.set_custom_approver(lambda tool, args: True)
    allowed, _ = gw_custom.verify_action("write_system_file", {"filename": "notes.txt"})
    assert allowed is True
    print("✅ دعم دوال الموافقة المخصصة يعمل بكفاءة.")


def test_reflection_engine():
    print("\n--- [3/5] اختبار محرك التصحيح الذاتي (Reflection Engine) ---")
    # اختبار الكشف الإرشادي الذاتي لإصلاح الروابط
    fixed, corrected, reason = reflection_engine.reflect_and_correct(
        "scrape_web_page",
        {"url": "example.com"},
        "Error: Invalid URL scheme"
    )
    assert fixed is True
    assert corrected.get("url") == "https://example.com"
    print(f"✅ التصحيح الذاتي للروابط: {corrected['url']} ({reason})")

    # اختبار الكشف الإرشادي الذاتي لامتدادات ملفات الإكسل
    fixed, corrected, reason = reflection_engine.reflect_and_correct(
        "generate_excel_report",
        {"filename": "my_report"},
        "Error: Invalid file format"
    )
    assert fixed is True
    assert corrected.get("filename") == "my_report.xlsx"
    print(f"✅ التصحيح الذاتي لامتداد الإكسل: {corrected['filename']} ({reason})")


def test_executor_structured():
    print("\n--- [4/5] اختبار المنفذ المحدث مع الأوامر المهيكلة والتنفيذ الفعلي ---")
    test_file = "test_framework_output.txt"

    # تنفيذ أمر مهيكل يحتوي على اسم أداة ومعاملات
    structured_cmd = {
        "tool": "write_system_file",
        "args": {
            "filename": test_file,
            "content": "Framework V2 Enterprise Enhancement Test Verified."
        }
    }
    res = executor.execute([structured_cmd])
    print(f"نتيجة التنفيذ المهيكل: {res}")
    assert os.path.exists(test_file)

    # قراءة الملف المنشأ
    read_cmd = {
        "tool": "read_system_file",
        "args": {"filename": test_file}
    }
    res_read = executor.execute([read_cmd])
    assert "Framework V2 Enterprise Enhancement" in res_read
    print("✅ كتابة وقراءة الملف بالمعاملات المهيكلة نجحت تماماً.")

    # تنظيف ملف الاختبار
    if os.path.exists(test_file):
        os.remove(test_file)


def test_dag_with_guardrails_and_context():
    print("\n--- [5/5] اختبار شبكة الـ DAG مع الحوكمة والحالة المشتركة ---")
    ctx = ExecutionContext(goal="DAG Integration Test")
    engine = DAGEngine(ctx)

    node1 = TaskNode(
        node_id="step_write",
        tool_key="write_system_file",
        input_mapping={"filename": "dag_temp.txt", "content": "DAG Engine Active"},
        output_key="write_status"
    )

    node2 = TaskNode(
        node_id="step_read",
        tool_key="read_system_file",
        input_mapping={"filename": "dag_temp.txt"},
        output_key="read_content",
        dependencies=["step_write"]
    )

    engine.add_nodes([node1, node2])
    result_ctx = engine.run()

    assert result_ctx.is_successful()
    assert result_ctx.get("read_content") == "DAG Engine Active"
    print("✅ تنفيذ شبكة الـ DAG بالكامل نجح وسجل الخطوات:")
    print(result_ctx.summary())

    if os.path.exists("dag_temp.txt"):
        os.remove("dag_temp.txt")


if __name__ == "__main__":
    print("==================================================")
    print("🚀 بدء تشغيل حزمة اختبار ترقيات الـ Framework...")
    print("==================================================")
    test_schema_bridge()
    test_guardrails()
    test_reflection_engine()
    test_executor_structured()
    test_dag_with_guardrails_and_context()
    print("\n" + "=" * 50)
    print("🎉 جميع الاختبارات (5/5) اجتازت بنجاح وبأعلى معايير الاستقرار!")
    print("==================================================")
