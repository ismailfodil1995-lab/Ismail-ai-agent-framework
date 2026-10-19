"""
Workflow Templates – orchestrator/templates.py
مستودع وقاموس مسارات عمل الـ DAG الجاهزة والمعيارية (WORKFLOW_TEMPLATES).
يتيح حفظ واستدعاء وبناء وتخصيص خطوط الإنتاج المعقدة عبر معرف المسار (Template ID).
"""

from typing import Any, Callable, Dict, List, Optional
from orchestrator.context import ExecutionContext
from orchestrator.node import TaskNode
from orchestrator.dag_engine import DAGEngine
from orchestrator.workflows import (
    create_lead_enrichment_pipeline,
    create_market_research_pipeline
)


def create_duckdb_analytics_pipeline(
    file_path: str,
    query: str = "",
    output_excel: str = "analytics_summary.xlsx"
) -> DAGEngine:
    """
    مسار عمل تحليل البيانات الضخمة عبر DuckDB:
    1. فحص بنية ومخطط الملف وإحصائياته (inspect_dataset_duckdb).
    2. تنفيذ استعلام SQL تجميعي متقدم (query_duckdb).
    3. حفظ النتائج في تقرير Excel منسق (generate_excel_report).
    """
    ctx = ExecutionContext(
        goal="DuckDB Big Data Analytics Pipeline",
        initial_data={
            "dataset_file": file_path,
            "custom_query": query,
            "excel_out": output_excel
        }
    )
    engine = DAGEngine(ctx)

    # 1. فحص المخطط
    node_inspect = TaskNode(
        node_id="inspect_step",
        tool_key="inspect_dataset_duckdb",
        input_mapping={"file_path": "context:dataset_file"},
        output_key="dataset_schema_report",
        description="فحص مخطط البيانات وحساب إجمالي السجلات"
    )

    # 2. تنفيذ استعلام SQL
    def _prepare_sql_query(c: ExecutionContext) -> str:
        q = c.get("custom_query", "")
        f = c.get("dataset_file", "")
        if q and str(q).strip():
            return str(q)
        return f"SELECT * FROM '{f}' LIMIT 100"

    node_query = TaskNode(
        node_id="query_step",
        tool_key="query_duckdb",
        input_mapping={
            "file_path": "context:dataset_file",
            "query": _prepare_sql_query
        },
        output_key="query_result_table",
        dependencies=["inspect_step"],
        description="تنفيذ استعلام DuckDB فائق السرعة"
    )

    # 3. إنشاء تقرير إكسل ملخص
    def _prepare_excel_rows(c: ExecutionContext):
        return [
            {
                "Source Dataset": c.get("dataset_file"),
                "Analysis Status": "Completed",
                "Schema Summary": str(c.get("dataset_schema_report", ""))[:250],
                "Query Preview": str(c.get("query_result_table", ""))[:300]
            }
        ]

    node_excel = TaskNode(
        node_id="excel_export_step",
        tool_key="generate_excel_report",
        input_mapping={
            "data": _prepare_excel_rows,
            "filename": "context:excel_out"
        },
        output_key="excel_export_result",
        dependencies=["query_step"],
        description="تصدير ملخص التحليل إلى ملف إكسل"
    )

    engine.add_nodes([node_inspect, node_query, node_excel])
    return engine


def create_ocr_document_pipeline(
    file_path: str,
    lang: str = "eng",
    output_summary: str = "ocr_document_summary.txt"
) -> DAGEngine:
    """
    مسار عمل المعالجة البصرية للمستندات والـ PDFs الممسوحة ضوئياً:
    1. استخراج النص البصري الشامل (extract_text_ocr).
    2. استخراج الجداول المهيكلة إن وجدت (extract_tables_ocr).
    3. حفظ النتيجة المجمعة في ملف نصي محلي (write_system_file).
    """
    ctx = ExecutionContext(
        goal="OCR Document & Table Extraction Pipeline",
        initial_data={
            "source_doc": file_path,
            "ocr_lang": lang,
            "output_doc": output_summary
        }
    )
    engine = DAGEngine(ctx)

    node_ocr_text = TaskNode(
        node_id="ocr_text_step",
        tool_key="extract_text_ocr",
        input_mapping={
            "file_path": "context:source_doc",
            "lang": "context:ocr_lang"
        },
        output_key="raw_ocr_text",
        description="استخراج النصوص البصرية من المستند"
    )

    node_ocr_tables = TaskNode(
        node_id="ocr_tables_step",
        tool_key="extract_tables_ocr",
        input_mapping={
            "file_path": "context:source_doc",
            "lang": "context:ocr_lang"
        },
        output_key="extracted_tables",
        dependencies=["ocr_text_step"],
        description="استخراج وتحليل الجداول المهيكلة"
    )

    def _compile_ocr_dossier(c: ExecutionContext) -> str:
        return (
            f"=== OCR Document Extraction Summary ===\n"
            f"Source: {c.get('source_doc')}\n\n"
            f"--- Extracted Text ---\n"
            f"{c.get('raw_ocr_text', 'No text recognized')}\n\n"
            f"--- Extracted Tables ---\n"
            f"{c.get('extracted_tables', 'No tables detected')}\n"
        )

    node_save = TaskNode(
        node_id="save_ocr_step",
        tool_key="write_system_file",
        input_mapping={
            "filename": "context:output_doc",
            "content": _compile_ocr_dossier
        },
        output_key="file_save_result",
        dependencies=["ocr_tables_step"],
        description="حفظ ملف المخرجات النهائي"
    )

    engine.add_nodes([node_ocr_text, node_ocr_tables, node_save])
    return engine


def create_multichannel_outreach_pipeline(
    client_info: str,
    recipient_email: str,
    subject: str = "Client Proposal & Next Steps"
) -> DAGEngine:
    """
    مسار عمل تأهيل العملاء والمراسلة الآلية عبر القنوات المتعددة:
    1. تأهيل وتحليل العميل (qualify_lead).
    2. توليد مقترح PDF رسمي (generate_pdf_report).
    3. إرسال بريد إلكتروني رسمي للعميل (send_email_report).
    """
    ctx = ExecutionContext(
        goal="Multi-Channel Client Outreach Pipeline",
        initial_data={
            "raw_client": client_info,
            "target_email": recipient_email,
            "email_subject": subject,
            "pdf_name": "client_proposal_official.pdf"
        }
    )
    engine = DAGEngine(ctx)

    node_qualify = TaskNode(
        node_id="qualify_step",
        tool_key="qualify_lead",
        input_mapping={"client_info": "context:raw_client"},
        output_key="lead_report",
        description="تأهيل العميل وتحليل المتطلبات"
    )

    def _prepare_proposal(c: ExecutionContext) -> str:
        return (
            f"Proposal Dossier\n"
            f"Client: {c.get('raw_client')}\n"
            f"Evaluation: {c.get('lead_report')}\n"
            f"Status: High-Priority Outreach"
        )

    node_pdf = TaskNode(
        node_id="pdf_proposal_step",
        tool_key="generate_pdf_report",
        input_mapping={
            "title": "Enterprise Automation Proposal",
            "content": _prepare_proposal,
            "filename": "context:pdf_name"
        },
        output_key="pdf_result",
        dependencies=["qualify_step"],
        description="إنشاء مستند المقترح بصيغة PDF"
    )

    def _email_body(c: ExecutionContext) -> str:
        return (
            f"Hello,\n\nYour proposal dossier has been prepared.\n"
            f"Summary: {c.get('lead_report', '')[:200]}\n"
            f"Attached document: {c.get('pdf_name')}\n\nBest regards,\nAI Agent"
        )

    node_email = TaskNode(
        node_id="email_step",
        tool_key="send_email_report",
        input_mapping={
            "recipient": "context:target_email",
            "subject": "context:email_subject",
            "body": _email_body
        },
        output_key="email_result",
        dependencies=["pdf_proposal_step"],
        description="إرسال تقرير المتابعة عبر البريد الإلكتروني"
    )

    engine.add_nodes([node_qualify, node_pdf, node_email])
    return engine


# =====================================================================
# قاموس القوالب الجاهزة (WORKFLOW_TEMPLATES)
# =====================================================================
WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "lead_enrichment": {
        "id": "lead_enrichment",
        "name": "Lead Enrichment & Proposal Pipeline",
        "category": "Sales & Business Development",
        "description": "تقييم وتأهيل العميل بالذكاء الاصطناعي، توليد ملفات Excel و PDF، وتنبيه n8n.",
        "required_inputs": ["client_info"],
        "optional_inputs": {
            "output_excel": "qualified_leads.xlsx",
            "output_pdf": "client_proposal.pdf"
        },
        "factory": create_lead_enrichment_pipeline
    },
    "market_research": {
        "id": "market_research",
        "name": "Market Intelligence & Web Scraping Pipeline",
        "category": "Research & Web Intelligence",
        "description": "بحث الويب المعمق، سحب وتحليل محتوى المواقع، وحفظ تقرير استخباري متكامل.",
        "required_inputs": ["search_query"],
        "optional_inputs": {
            "target_url": "https://example.com",
            "output_filename": "market_research_summary.txt"
        },
        "factory": create_market_research_pipeline
    },
    "duckdb_analytics": {
        "id": "duckdb_analytics",
        "name": "DuckDB Big Data Analytics Pipeline",
        "category": "Data Engineering & Analytics",
        "description": "تحليل واستعلام ملفات CSV و Parquet الضخمة بسرعة خارقة وتوليد تقرير Excel تنفيذي.",
        "required_inputs": ["file_path"],
        "optional_inputs": {
            "query": "",
            "output_excel": "analytics_summary.xlsx"
        },
        "factory": create_duckdb_analytics_pipeline
    },
    "ocr_document_processing": {
        "id": "ocr_document_processing",
        "name": "OCR Document & Table Extraction Pipeline",
        "category": "Document Processing & OCR",
        "description": "استخراج النصوص والجداول من المستندات والصور والـ PDFs الممسوحة ضوئياً وتوثيقها.",
        "required_inputs": ["file_path"],
        "optional_inputs": {
            "lang": "eng",
            "output_summary": "ocr_document_summary.txt"
        },
        "factory": create_ocr_document_pipeline
    },
    "multichannel_outreach": {
        "id": "multichannel_outreach",
        "name": "Multi-Channel Automated Outreach Pipeline",
        "category": "Marketing & CRM Automation",
        "description": "تأهيل العميل آلياً، إنشاء مقترح PDF رسمي، وإرسال بريد إلكتروني تنفيذي فوري.",
        "required_inputs": ["client_info", "recipient_email"],
        "optional_inputs": {
            "subject": "Client Proposal & Next Steps"
        },
        "factory": create_multichannel_outreach_pipeline
    }
}


def get_workflow_template(template_id: str) -> Optional[Dict[str, Any]]:
    """استرجاع مواصفات قالب مسار العمل بناءً على الـ ID"""
    clean_id = template_id.strip().lower()
    if clean_id in WORKFLOW_TEMPLATES:
        return WORKFLOW_TEMPLATES[clean_id]

    for key, tpl in WORKFLOW_TEMPLATES.items():
        if key in clean_id or clean_id in key:
            return tpl
    return None


def list_workflow_templates() -> List[Dict[str, Any]]:
    """سرد كافة قوالب مسارات العمل المتاحة مع وصفها ومعاملاتها"""
    templates = []
    for tid, tpl in WORKFLOW_TEMPLATES.items():
        templates.append({
            "id": tid,
            "name": tpl["name"],
            "category": tpl["category"],
            "description": tpl["description"],
            "required_inputs": tpl["required_inputs"],
            "optional_inputs": tpl["optional_inputs"]
        })
    return templates


def register_workflow_template(template_id: str, template_data: Dict[str, Any]) -> None:
    """تسجيل مسار عمل DAG جديد ديناميكياً في المستودع"""
    if not template_id or "factory" not in template_data:
        raise ValueError("Template registration requires a valid 'template_id' and 'factory' callable.")
    template_data["id"] = template_id
    WORKFLOW_TEMPLATES[template_id] = template_data


def instantiate_workflow(template_id: str, **kwargs) -> DAGEngine:
    """
    استدعاء وبناء كائن DAGEngine الجاهز للتنفيذ بناءً على معرف القالب (template_id)
    مع التحقق التلقائي من اكتمال المعاملات المطلوبة.
    """
    tpl = get_workflow_template(template_id)
    if not tpl:
        available_ids = ", ".join(WORKFLOW_TEMPLATES.keys())
        raise KeyError(f"Workflow template '{template_id}' not found. Available templates: [{available_ids}]")

    # التحقق من المدخلات الإلزامية
    missing = [req for req in tpl["required_inputs"] if req not in kwargs or kwargs[req] is None]
    if missing:
        raise ValueError(
            f"Missing required inputs for workflow template '{template_id}': {missing}. "
            f"Required: {tpl['required_inputs']}, Optional: {list(tpl['optional_inputs'].keys())}"
        )

    # دمج المعاملات الافتراضية الاختيارية
    combined_args = dict(tpl.get("optional_inputs", {}))
    combined_args.update({k: v for k, v in kwargs.items() if v is not None})

    factory: Callable[..., DAGEngine] = tpl["factory"]
    return factory(**combined_args)
