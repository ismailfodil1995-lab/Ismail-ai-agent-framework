"""
Orchestrator: طبقة التنسيق الذاتي وإدارة الرسوم البيانية الموجهة (DAG Engine)
"""
from orchestrator.context import ExecutionContext, ExecutionRecord
from orchestrator.node import TaskNode
from orchestrator.dag_engine import DAGEngine
from orchestrator.workflows import (
    create_lead_enrichment_pipeline,
    create_market_research_pipeline
)
from orchestrator.templates import (
    WORKFLOW_TEMPLATES,
    get_workflow_template,
    list_workflow_templates,
    instantiate_workflow,
    register_workflow_template
)

__all__ = [
    "ExecutionContext",
    "ExecutionRecord",
    "TaskNode",
    "DAGEngine",
    "create_lead_enrichment_pipeline",
    "create_market_research_pipeline",
    "WORKFLOW_TEMPLATES",
    "get_workflow_template",
    "list_workflow_templates",
    "instantiate_workflow",
    "register_workflow_template"
]
