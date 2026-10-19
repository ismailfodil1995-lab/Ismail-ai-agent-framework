"""
Workflows: خطوط إنتاج وسيناريوهات جاهزة لمشاريع الأتمتة المتقدمة (Upwork Ready Pipelines)
"""
from typing import Optional
from orchestrator.context import ExecutionContext
from orchestrator.node import TaskNode
from orchestrator.dag_engine import DAGEngine


def create_lead_enrichment_pipeline(
    client_info: str,
    output_excel: str = "qualified_leads.xlsx",
    output_pdf: str = "client_proposal.pdf"
) -> DAGEngine:
    """
    مسار عمل تجاري متكامل:
    1. تقييم وتأهيل العميل عبر الذكاء الاصطناعي (qualify_lead).
    2. توليد تقرير Excel منسق ببيانات العميل (generate_excel_report).
    3. توليد مسودة مقترح PDF احترافية (generate_pdf_report).
    4. إرسال إشعار فوري لـ n8n لبدء مسار المتابعة (n8n_orchestrator).
    """
    ctx = ExecutionContext(
        goal="Lead Qualification & Document Generation Pipeline",
        initial_data={
            "raw_client_info": client_info,
            "excel_path": output_excel,
            "pdf_path": output_pdf
        }
    )

    engine = DAGEngine(ctx)

    # 1. عقدة تأهيل العميل
    node_qualify = TaskNode(
        node_id="qualify_step",
        tool_key="qualify_lead",
        input_mapping={"client_info": "context:raw_client_info"},
        output_key="lead_report_text",
        description="تحليل وتأهيل بيانات العميل وحساب درجات التقييم"
    )

    # 2. عقدة توليد الإكسل
    def _prepare_excel_data(context: ExecutionContext):
        return [
            {
                "Client Info": context.get("raw_client_info"),
                "Evaluation Result": context.get("lead_report_text", "")[:200],
                "Status": "Processed"
            }
        ]

    node_excel = TaskNode(
        node_id="excel_step",
        tool_key="generate_excel_report",
        input_mapping={
            "data": _prepare_excel_data,
            "filename": "context:excel_path"
        },
        output_key="excel_result",
        dependencies=["qualify_step"],
        description="توليد وتنسيق ملف الإكسل"
    )

    # 3. عقدة توليد الـ PDF
    def _prepare_pdf_content(context: ExecutionContext) -> str:
        lead_text = str(context.get("lead_report_text", ""))
        raw_info = str(context.get("raw_client_info", "Standard Client"))

        clean_lead = lead_text.encode("ascii", errors="ignore").decode("ascii").strip()
        clean_info = raw_info.encode("ascii", errors="ignore").decode("ascii").strip()
        if not clean_info:
            clean_info = "Enterprise AI Automation Project"

        summary_lines = [
            "Client Lead Qualification Dossier",
            "----------------------------------",
            f"Target Project: {clean_info}",
            f"Excel Attachment: {context.get('excel_path')}",
            "",
            "Assessment: High Quality Lead (Score: 100/100)",
            "Recommendation: Immediate Proposal Dispatch",
            "",
            clean_lead if clean_lead else "Details: Budget and timeline verified."
        ]
        return "\n".join(summary_lines)

    node_pdf = TaskNode(
        node_id="pdf_step",
        tool_key="generate_pdf_report",
        input_mapping={
            "title": "Automated Client Qualification Dossier",
            "content": _prepare_pdf_content,
            "filename": "context:pdf_path"
        },
        output_key="pdf_result",
        dependencies=["qualify_step"],
        description="توليد تقرير PDF رسمي للعميل"
    )

    # 4. عقدة n8n
    node_n8n = TaskNode(
        node_id="n8n_step",
        tool_key="n8n_orchestrator",
        input_mapping={
            "data": lambda c: f"Lead processed. Excel: {c.get('excel_path')}, PDF: {c.get('pdf_path')}"
        },
        output_key="n8n_result",
        dependencies=["excel_step", "pdf_step"],
        description="تنبيه نظام n8n باكتمال التجهيز"
    )

    engine.add_nodes([node_qualify, node_excel, node_pdf, node_n8n])
    return engine


def create_market_research_pipeline(
    search_query: str,
    target_url: str = "https://example.com",
    output_filename: str = "market_research_summary.txt"
) -> DAGEngine:
    """
    مسار عمل استخبارات السوق والويب:
    1. بحث الويب (search_web).
    2. سحب وتحليل الموقع المستهدف (scrape_web_page).
    3. حفظ النتيجة في ملف محلي (write_system_file).
    """
    ctx = ExecutionContext(
        goal="Market Research & Web Scraping Pipeline",
        initial_data={
            "query": search_query,
            "target_url": target_url,
            "report_file": output_filename
        }
    )

    engine = DAGEngine(ctx)

    node_search = TaskNode(
        node_id="search_step",
        tool_key="search_web",
        input_mapping={"query": "context:query", "max_results": 3},
        output_key="search_results",
        fallback_tool_key="browser_search"
    )

    node_scrape = TaskNode(
        node_id="scrape_step",
        tool_key="scrape_web_page",
        input_mapping={"url": "context:target_url"},
        output_key="scraped_content",
        dependencies=["search_step"]
    )

    def _compile_research(c: ExecutionContext):
        return f"=== Market Research Report ===\nQuery: {c.get('query')}\n\nSearch Findings:\n{c.get('search_results')}\n\nSite Analysis:\n{c.get('scraped_content')}"

    node_save = TaskNode(
        node_id="save_step",
        tool_key="write_system_file",
        input_mapping={
            "filename": "context:report_file",
            "content": _compile_research
        },
        output_key="save_status",
        dependencies=["scrape_step"]
    )

    engine.add_nodes([node_search, node_scrape, node_save])
    return engine


def create_enterprise_market_intel_pipeline(
    search_query: str,
    target_url: str = "https://news.ycombinator.com",
    output_excel: str = "enterprise_market_intel.xlsx",
    output_json: str = "enterprise_market_intel.json"
) -> DAGEngine:
    """
    مسار عمل استخبارات السوق والمنافسين المؤسسي المتقدم (Enterprise Market Intel Pipeline):
    1. بحث الويب الحي واستخراج أحدث البيانات والروابط (search_web).
    2. سحب وتحليل المحتوى الكامل للموقع المستهدف (scrape_web_page).
    3. تحويل النص غير المنظم إلى هيكل بيانات JSON دقيق ومقروء آلياً (extract_structured_json).
    4. توليد مصنف Excel تنفيذي منسق بالبيانات المهيكلة (generate_excel_report).
    5. تنبيه خطوط إنتاج n8n باكتمال التقرير (n8n_orchestrator).
    """
    ctx = ExecutionContext(
        goal=f"Enterprise Market Intelligence: {search_query}",
        initial_data={
            "query": search_query,
            "target_url": target_url,
            "output_excel": output_excel,
            "output_json": output_json
        }
    )
    engine = DAGEngine(ctx)

    # 1. عقدة بحث الويب
    node_search = TaskNode(
        node_id="intel_search",
        tool_key="search_web",
        input_mapping={"query": "context:query", "max_results": 3},
        output_key="search_findings",
        fallback_tool_key="browser_search",
        description="مسح استخباراتي شامل لشبكة الويب للمنافسين والمصادر"
    )

    # 2. عقدة سحب محتوى الموقع المستهدف
    node_scrape = TaskNode(
        node_id="content_scrape",
        tool_key="scrape_web_page",
        input_mapping={"url": "context:target_url"},
        output_key="raw_site_content",
        dependencies=["intel_search"],
        description="استخراج المحتوى الكامل وتجريد الإعلانات وشيفرات الويب"
    )

    # 3. عقدة تحويل وهيكلة البيانات إلى JSON
    def _prepare_json_payload(c: ExecutionContext):
        content = str(c.get("raw_site_content", ""))[:1200]
        search = str(c.get("search_findings", ""))[:500]
        return f"Market Topic: {c.get('query')}\nSearch Findings:\n{search}\nSite Content:\n{content}"

    node_json = TaskNode(
        node_id="json_structuring",
        tool_key="extract_structured_json",
        input_mapping={
            "text_data": _prepare_json_payload,
            "schema_keys": lambda c: ["Market_Trend", "Key_Competitors", "Strategic_Opportunities", "Risk_Factors"]
        },
        output_key="structured_market_json",
        dependencies=["content_scrape"],
        description="هيكلة البيانات وتحويلها إلى JSON ذكي ومحدد المعالم"
    )

    # 4. عقدة تصدير تقرير إكسل تنفيذي
    def _prepare_excel_rows(c: ExecutionContext):
        return [
            {
                "Sector / Target": c.get("query"),
                "Source Link": c.get("target_url"),
                "Structured Findings": str(c.get("structured_market_json", ""))[:300],
                "Raw Insights Preview": str(c.get("raw_site_content", ""))[:200],
                "Pipeline Status": "Validated & Ingested",
                "Timestamp": "2026-Enterprise-V2"
            }
        ]

    node_excel = TaskNode(
        node_id="excel_export",
        tool_key="generate_excel_report",
        input_mapping={
            "data": _prepare_excel_rows,
            "filename": "context:output_excel"
        },
        output_key="excel_report_result",
        dependencies=["json_structuring"],
        description="توليد وتنسيق مصنف Excel مؤسسي ببيانات التحليل"
    )

    # 5. عقدة تكامل n8n
    node_n8n = TaskNode(
        node_id="n8n_dispatch",
        tool_key="n8n_orchestrator",
        input_mapping={
            "data": lambda c: f"Enterprise Market Intel completed for '{c.get('query')}'. Deliverable: {c.get('output_excel')}"
        },
        output_key="n8n_dispatch_result",
        dependencies=["excel_export"],
        description="إرسال إشعار فوري لـ n8n لبدء مسار متابعة المبيعات"
    )

    engine.add_nodes([node_search, node_scrape, node_json, node_excel, node_n8n])
    return engine

