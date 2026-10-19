"""
api_server.py - طبقة الـ API الموحدة للـ AI Agent Framework
==============================================================
تربط جميع مكونات الـ Framework في نقطة دخول واحدة:
    Planner -> Executor -> Guardrails -> DAGEngine -> WORKFLOW_TEMPLATES

تشغيل السيرفر:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

نقاط الاتصال المتاحة:
    POST /run           - تشغيل أمر نصي عبر Planner + Executor
    POST /dag           - تنفيذ مسار DAG مخصص مباشرة
    POST /workflow      - تشغيل قالب عمل جاهز من WORKFLOW_TEMPLATES
    GET  /tools         - قائمة كاملة بجميع الأدوات المسجلة ومخططاتها
    GET  /health        - فحص جاهزية النظام
    GET  /audit         - سجل قرارات الـ Guardrails الأمنية
    GET  /workflows     - قائمة القوالب الجاهزة
    GET  /docs          - توثيق Swagger التلقائي (مدمج مع FastAPI)
"""

import asyncio
import collections
import datetime
import logging
import time
import uuid
from contextlib import asynccontextmanager
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request, Security, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# --- اعداد نظام السجلات (Structured Logging) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ai_agent.api")


# --- تحميل مكونات الـ Framework عند بدء التشغيل ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle manager"""
    logger.info("=" * 60)
    logger.info("AI Agent API Server - Starting up...")

    try:
        import tools  # noqa - triggers __init__.py auto-loader
        from services.tool_registry_bridge import tool_bridge
        tool_count = len(tool_bridge.tools)
        logger.info(f"[OK] Tool Registry loaded -> {tool_count} tools available")
    except Exception as e:
        logger.warning(f"[WARN] Tool Registry partial load: {e}")

    try:
        from planner import planner  # noqa
        logger.info("[OK] Planner loaded")
    except Exception as e:
        logger.warning(f"[WARN] Planner load issue: {e}")

    try:
        from executor import executor  # noqa
        logger.info("[OK] Executor loaded")
    except Exception as e:
        logger.warning(f"[WARN] Executor load issue: {e}")

    logger.info("[READY] API Server is READY. Documentation at /docs")
    logger.info("=" * 60)

    yield

    logger.info("AI Agent API Server - Shutting down.")


# --- انشاء تطبيق FastAPI ---
API_VERSION = "2.1.0"

app = FastAPI(
    title="AI Agent Framework API",
    description=(
        "REST gateway for the AI Agent Framework.\n\n"
        "Provides access to: Planner, Executor, DAG Engine, "
        "Guardrails, Workflow Templates, and 29+ registered tools."
    ),
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- CORS Middleware ---
# قراءة القائمة المسموح بها من البيئة؛ إذا لم تُحدَّد يُقبَل localhost فقط
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
ALLOWED_ORIGINS: List[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "X-API-Key", "Content-Type"],
)

# --- Rate Limiting (sliding-window، in-memory) ---
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_RPM", "60"))   # طلبات في الدقيقة
_rate_store: Dict[str, collections.deque] = {}


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    """حد أقصى RATE_LIMIT_RPM طلباً في الدقيقة لكل IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window_start = now - 60.0

    bucket = _rate_store.setdefault(client_ip, collections.deque())
    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= _RATE_LIMIT:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": "60"}
        )

    bucket.append(now)
    return await call_next(request)


# --- Middleware: تسجيل كل طلب مع مدة الاستجابة ---
@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] -> {request.method} {request.url.path}")
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(f"[{request_id}] <- {response.status_code} | {duration_ms}ms")
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# --- طبقة الأمان والمصادقة (API Security & Authentication Layer) ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="API Key via X-API-Key header")
bearer_security = HTTPBearer(auto_error=False, description="API Key via Bearer token")

def get_configured_api_key() -> str:
    return os.getenv("API_KEY", "").strip()

async def verify_api_key(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_security)
) -> str:
    """
    التحقق من صحة مفتاح الـ API عبر X-API-Key أو Authorization: Bearer.
    يحمي المسارات الحساسة للوكيل، مع تفعيل تصريح تلقائي محلي للـ Demo و Swagger عبر localhost.
    """
    expected_key = get_configured_api_key()
    client_ip = request.client.host if request.client else "127.0.0.1"

    provided_key = header_key or (bearer_token.credentials if bearer_token else None)

    # السماح التلقائي للاختبارات المحلية و Swagger UI من localhost
    if not provided_key and client_ip in ("127.0.0.1", "localhost", "::1", "testclient"):
        return expected_key or "local-demo-authorized"

    if expected_key and provided_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing API Key. Provide a valid 'X-API-Key' or 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return provided_key or "demo-key"


# =============================================================================
# Pydantic Schemas
# =============================================================================

class RunRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=4000,
        description="The command or question to execute",
        examples=["search for AI automation trends"]
    )
    parallel: bool = Field(False, description="Run multiple tasks in parallel via asyncio.gather")
    session_id: Optional[str] = Field(None, description="Session identifier for request tracking")


class RunResponse(BaseModel):
    success: bool
    result: str
    plan: Optional[Dict[str, Any]] = None
    session_id: str
    duration_ms: float
    timestamp: str


class DAGNodeSpec(BaseModel):
    node_id: str = Field(..., description="Unique node identifier")
    tool_key: str = Field(..., description="Tool key as registered in AVAILABLE_TOOLS")
    input_mapping: Dict[str, Any] = Field(default_factory=dict, description="Input mapping (supports context:key syntax)")
    output_key: Optional[str] = Field(None, description="Key to store the output in execution context")
    dependencies: List[str] = Field(default_factory=list, description="List of node_ids that must execute first")
    description: str = Field("", description="Human-readable description of this node's purpose")
    retries: int = Field(2, ge=1, le=5, description="Number of retry attempts on failure")


class DAGRequest(BaseModel):
    goal: str = Field(..., description="High-level goal of this workflow")
    nodes: List[DAGNodeSpec] = Field(..., min_length=1, description="List of DAG nodes to execute")
    initial_data: Dict[str, Any] = Field(default_factory=dict, description="Initial data loaded into execution context")
    stop_on_failure: bool = Field(True, description="Halt the entire pipeline on first node failure")


class DAGResponse(BaseModel):
    success: bool
    session_id: str
    goal: str
    steps_executed: int
    errors: List[str]
    history: List[Dict[str, Any]]
    data_keys: List[str]
    duration_ms: float
    mermaid_diagram: Optional[str] = None
    timestamp: str


class WorkflowRequest(BaseModel):
    template_id: str = Field(
        ..., description="Template identifier",
        examples=["lead_enrichment", "market_research", "duckdb_analytics"]
    )
    params: Dict[str, Any] = Field(default_factory=dict, description="Template-specific parameters")


class WorkflowResponse(BaseModel):
    success: bool
    template_id: str
    session_id: str
    steps_executed: int
    errors: List[str]
    history: List[Dict[str, Any]]
    duration_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="API & Framework version")
    tools_count: int = Field(..., description="Total registered tools")
    guardrails_mode: str = Field(..., description="Current guardrails mode")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    timestamp: str = Field(..., description="Current ISO timestamp")
    engines: Dict[str, Any] = Field(default_factory=dict, description="Health status of core agent engines")
    tools_health: Dict[str, Any] = Field(default_factory=dict, description="Detailed tool registry readiness and categorization")
    environment: Dict[str, Any] = Field(default_factory=dict, description="Storage and environment readiness")


_server_start_time = time.time()


# =============================================================================
# Endpoints
# =============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Comprehensive system & engines health check",
    tags=["System"]
)
async def health_check():
    """
    فحص شامل وعميق لصحة المحركات الأساسية والأدوات وبيئة التشغيل:
    - محركات LLM, Planner, Executor, Guardrails, Reflection, DAG Orchestrator
    - فحص سلامة دوال جميع الأدوات المسجلة وتوزيعها الوظيفي
    - التحقق من مجلدات التخزين والبيئة المحلية
    """
    overall_status = "healthy"
    engines: Dict[str, Any] = {}
    tools_health: Dict[str, Any] = {}
    environment: Dict[str, Any] = {}

    # 1. فحص محرك الأدوات وسلامة الدوال (Tools Integrity)
    unhealthy_tools = []
    category_counts = {}
    total_tools = 0

    try:
        from services.tool_registry_bridge import tool_bridge
        all_tools = tool_bridge.tools
        total_tools = len(all_tools)

        for name, data in all_tools.items():
            fn = data.get("fn") or data.get("function")
            if not callable(fn):
                unhealthy_tools.append(name)

        from planner import TOOL_CATEGORIES
        for cat, tool_list in TOOL_CATEGORIES.items():
            category_counts[cat] = len([t for t in tool_list if t in all_tools])

        tools_health = {
            "status": "ready" if not unhealthy_tools else "degraded",
            "total_registered": total_tools,
            "executable_count": total_tools - len(unhealthy_tools),
            "unhealthy_tools": unhealthy_tools,
            "categories_breakdown": category_counts
        }
        if unhealthy_tools:
            overall_status = "degraded"
    except Exception as e:
        tools_health = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    # 2. فحص المحركات الأساسية (Core Engines)
    # 2.1 محرك التخطيط (Planner)
    try:
        from planner import planner, TOOL_CATEGORIES
        engines["planner"] = {
            "status": "ready",
            "type": "llm_dynamic_sparse",
            "sparse_categories_count": len(TOOL_CATEGORIES),
            "zero_hardcoding": True
        }
    except Exception as e:
        engines["planner"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    # 2.2 محرك التنفيذ (Executor)
    try:
        from executor import executor
        engines["executor"] = {
            "status": "ready",
            "max_retries": executor.max_retries,
            "supports_async": True,
            "supports_parallel": True
        }
    except Exception as e:
        engines["executor"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"

    # 2.3 بوابات الحوكمة والأمان (Guardrails)
    try:
        from services.guardrails import guardrails
        from config import GUARDRAILS_MODE
        engines["guardrails"] = {
            "status": "active",
            "mode": GUARDRAILS_MODE,
            "audit_trail_count": len(guardrails.get_audit_trail())
        }
    except Exception as e:
        engines["guardrails"] = {"status": "unknown", "error": str(e)}

    # 2.4 محرك التصحيح الذاتي (Reflection Engine)
    try:
        from services.reflection_engine import reflection_engine
        engines["reflection"] = {
            "status": "active",
            "max_attempts": reflection_engine.max_attempts
        }
    except Exception as e:
        engines["reflection"] = {"status": "error", "error": str(e)}

    # 2.5 محرك مسارات العمل (DAG Orchestrator)
    try:
        import orchestrator.workflows as wf
        pipelines = [f for f in dir(wf) if f.startswith("create_") and callable(getattr(wf, f))]
        engines["orchestrator"] = {
            "status": "ready",
            "workflow_pipelines_count": len(pipelines),
            "available_pipelines": pipelines
        }
    except Exception as e:
        engines["orchestrator"] = {"status": "unknown", "error": str(e)}

    # 2.6 مزود الذكاء الاصطناعي (LLM Provider)
    try:
        from config import OLLAMA_URL, MODEL_NAME, TIMEOUT
        engines["llm"] = {
            "status": "configured",
            "model": MODEL_NAME,
            "endpoint": OLLAMA_URL,
            "timeout_seconds": TIMEOUT
        }
    except Exception as e:
        engines["llm"] = {"status": "error", "error": str(e)}

    # 3. فحص بيئة العمل والتخزين (Environment & Storage)
    try:
        import os
        import sys
        uploads_exists = os.path.isdir("uploads")
        if not uploads_exists:
            os.makedirs("uploads", exist_ok=True)
            uploads_exists = True

        environment = {
            "status": "ready",
            "uploads_dir": "uploads",
            "uploads_writable": os.access("uploads", os.W_OK),
            "python_version": sys.version.split()[0],
            "os_platform": sys.platform
        }
    except Exception as e:
        environment = {"status": "warning", "error": str(e)}

    # وضع نمط الحوكمة الحالي
    guardrails_mode = engines.get("guardrails", {}).get("mode", "unknown")

    return HealthResponse(
        status=overall_status,
        version=API_VERSION,
        tools_count=total_tools,
        guardrails_mode=guardrails_mode,
        uptime_seconds=round(time.time() - _server_start_time, 1),
        timestamp=datetime.datetime.now().isoformat(),
        engines=engines,
        tools_health=tools_health,
        environment=environment
    )


@app.get(
    "/tools",
    dependencies=[Depends(verify_api_key)],
    summary="List all registered tools",
    tags=["Tools"]
)
async def list_tools():
    """Returns all registered tools with their parameter schemas."""
    try:
        from services.tool_registry_bridge import tool_bridge
        metadata = tool_bridge.get_all_tools_metadata()
        tools_list = [
            {
                "tool_key": key,
                "name": info.get("name", key),
                "description": info.get("description", ""),
                "parameters": info.get("parameters", {})
            }
            for key, info in sorted(metadata.items())
        ]
        return {
            "total": len(tools_list),
            "tools": tools_list,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load tools registry: {str(e)}")


@app.get(
    "/audit",
    dependencies=[Depends(verify_api_key)],
    summary="Guardrails security audit trail",
    tags=["Security"]
)
async def get_audit_trail(limit: int = 50):
    """Returns the last N security decisions logged by the Guardrails gateway."""
    try:
        from services.guardrails import guardrails
        trail = guardrails.get_audit_trail()
        trail_sorted = list(reversed(trail))[:limit]
        return {
            "total_records": len(trail),
            "showing": len(trail_sorted),
            "audit_trail": trail_sorted,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching audit trail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load audit trail: {str(e)}")


@app.post(
    "/run",
    dependencies=[Depends(verify_api_key)],
    response_model=RunResponse,
    summary="Execute a natural language command (Planner -> Executor)",
    tags=["Execution"]
)
async def run_query(request: RunRequest):
    """
    **Main entry point for the AI Agent Framework.**

    Routes the query through:
    1. **Planner** - Analyzes intent and selects the right tool or plan
    2. **Executor** - Runs the plan with Guardrails + Self-Healing Reflection Loop

    Supports:
    - Single tool calls: `"search_web AI automation trends"`
    - Multi-step sequential: `"read file report.txt then send email"`
    - Parallel execution: set `parallel: true`
    - Arabic and English queries
    """
    start = time.perf_counter()
    session_id = request.session_id or str(uuid.uuid4())[:8]

    logger.info(f"[/run] session={session_id} | query='{request.query[:80]}' | parallel={request.parallel}")

    # Step 1: Planning
    plan = None
    try:
        from planner import planner
        plan = planner.make_plan(request.query)
        logger.info(f"[/run] session={session_id} | plan_type={plan.get('type', 'unknown')}")
    except Exception as e:
        logger.warning(f"[/run] Planner failed: {e} - falling back to direct execution")

    # Step 2: Build executor input from plan and route to correct execution path
    executor_input: Any = request.query

    if plan:
        plan_type = plan.get("type", "llm")

        if plan_type == "tool":
            # Single-tool plan: pass a proper command dict directly to the executor.
            # {"tool": <name>, "args": <dict>} is the format _resolve_tool_and_args expects.
            tool_name = plan.get("tool", "")
            tool_args  = plan.get("args", {})
            # Normalise: if tool_name contains spaces it's a legacy text command —
            # keep it as a plain string so the text-matching path in _resolve_tool_and_args
            # can handle it, otherwise use the structured dict form.
            if " " in tool_name.strip() and not tool_args:
                executor_input = tool_name          # e.g. "list files"
            else:
                executor_input = {"tool": tool_name, "args": tool_args}
            logger.info(f"[/run] session={session_id} | routing=single_tool | tool='{tool_name}'")

        elif plan_type == "plan":
            # Multi-step plan: each step must be a proper command dict with "tool" + "args".
            raw_steps = plan.get("steps", [])
            executor_input = []
            for step in raw_steps:
                if isinstance(step, dict):
                    step_tool = step.get("tool", "")
                    step_args = step.get("args", {})
                    if " " in step_tool.strip() and not step_args:
                        executor_input.append(step_tool)
                    else:
                        executor_input.append({"tool": step_tool, "args": step_args})
                else:
                    executor_input.append(str(step))
            if not executor_input:
                executor_input = [request.query]
            logger.info(f"[/run] session={session_id} | routing=multi_step | steps={len(executor_input)}")

        else:
            # plan_type == "llm" or unknown: pass raw query for direct LLM/fallback handling
            executor_input = request.query
            logger.info(f"[/run] session={session_id} | routing=llm_fallback")

    # Step 3: Execute via the Executor (async)
    try:
        from executor import executor
        result = await executor.execute_async(executor_input, parallel=request.parallel)
    except Exception as e:
        logger.error(f"[/run] Executor error: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    success = not result.lower().startswith("error") and not result.lower().startswith("[security")

    logger.info(f"[/run] session={session_id} | success={success} | duration={duration_ms}ms")

    return RunResponse(
        success=success,
        result=result,
        plan=plan,
        session_id=session_id,
        duration_ms=duration_ms,
        timestamp=datetime.datetime.now().isoformat()
    )


@app.post(
    "/dag",
    dependencies=[Depends(verify_api_key)],
    response_model=DAGResponse,
    summary="Execute a custom DAG workflow",
    tags=["DAG Engine"]
)
async def run_dag(request: DAGRequest):
    """
    **Execute a custom Directed Acyclic Graph (DAG) workflow.**

    The engine guarantees:
    - Topological sort for correct execution order
    - Cycle detection (returns 422 if cycles are detected)
    - Smart skipping of nodes whose dependencies failed
    - Full execution history with timing per node

    **Example payload:**
    ```json
    {
      "goal": "Research and save market data",
      "nodes": [
        {
          "node_id": "s1",
          "tool_key": "search_web",
          "input_mapping": {"query": "AI trends 2026"},
          "output_key": "search_out"
        },
        {
          "node_id": "s2",
          "tool_key": "write_system_file",
          "input_mapping": {"filename": "output.txt", "content": "context:search_out"},
          "dependencies": ["s1"]
        }
      ]
    }
    ```
    """
    start = time.perf_counter()
    logger.info(f"[/dag] goal='{request.goal}' | nodes={len(request.nodes)}")

    try:
        from orchestrator.context import ExecutionContext
        from orchestrator.node import TaskNode
        from orchestrator.dag_engine import DAGEngine

        ctx = ExecutionContext(
            goal=request.goal,
            initial_data=request.initial_data
        )
        engine = DAGEngine(ctx)

        for node_spec in request.nodes:
            task_node = TaskNode(
                node_id=node_spec.node_id,
                tool_key=node_spec.tool_key,
                input_mapping=node_spec.input_mapping,
                output_key=node_spec.output_key,
                dependencies=node_spec.dependencies,
                description=node_spec.description,
                retries=node_spec.retries
            )
            engine.add_node(task_node)

        # Validate DAG before execution
        try:
            execution_order = engine.validate()
            logger.info(f"[/dag] Execution order: {execution_order}")
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"DAG Validation Error: {str(ve)}"
            )

        # Run in thread (node.execute is synchronous)
        result_ctx = await asyncio.to_thread(engine.run, stop_on_failure=request.stop_on_failure)

        try:
            mermaid = engine.to_mermaid()
        except Exception:
            mermaid = None

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        snapshot = result_ctx.snapshot()

        logger.info(
            f"[/dag] Completed | steps={snapshot['history_count']} | "
            f"errors={len(snapshot['errors'])} | duration={duration_ms}ms"
        )

        return DAGResponse(
            success=result_ctx.is_successful(),
            session_id=result_ctx.session_id,
            goal=request.goal,
            steps_executed=snapshot["history_count"],
            errors=snapshot["errors"],
            history=snapshot["records"],
            data_keys=snapshot["data_keys"],
            duration_ms=duration_ms,
            mermaid_diagram=mermaid,
            timestamp=datetime.datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[/dag] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DAG execution failed: {str(e)}")


@app.post(
    "/workflow",
    dependencies=[Depends(verify_api_key)],
    response_model=WorkflowResponse,
    summary="Run a pre-built workflow template",
    tags=["Workflow Templates"]
)
async def run_workflow(request: WorkflowRequest):
    """
    **Trigger a ready-made workflow from WORKFLOW_TEMPLATES.**

    Available templates:

    | template_id | Description | Required Params |
    |---|---|---|
    | `lead_enrichment` | Qualify lead + Excel + PDF + n8n | `client_info` |
    | `market_research` | Web search + scraping + save report | `search_query`, `target_url` |
    | `duckdb_analytics` | Big data analysis + Excel report | `file_path` |
    """
    start = time.perf_counter()
    logger.info(f"[/workflow] template='{request.template_id}' | params={list(request.params.keys())}")

    # Build template registry
    TEMPLATE_REGISTRY: Dict[str, Any] = {}

    try:
        from orchestrator.workflows import (
            create_lead_enrichment_pipeline,
            create_market_research_pipeline,
            create_enterprise_market_intel_pipeline
        )
        TEMPLATE_REGISTRY["lead_enrichment"] = create_lead_enrichment_pipeline
        TEMPLATE_REGISTRY["market_research"] = create_market_research_pipeline
        TEMPLATE_REGISTRY["enterprise_market_intel"] = create_enterprise_market_intel_pipeline
    except Exception as e:
        logger.warning(f"[/workflow] Could not load standard workflows: {e}")

    try:
        from orchestrator.templates import create_duckdb_analytics_pipeline
        TEMPLATE_REGISTRY["duckdb_analytics"] = create_duckdb_analytics_pipeline
    except Exception as e:
        logger.warning(f"[/workflow] Could not load duckdb template: {e}")

    template_id = request.template_id.lower().strip()
    if template_id not in TEMPLATE_REGISTRY:
        available = list(TEMPLATE_REGISTRY.keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Template '{template_id}' not found.",
                "available_templates": available
            }
        )

    factory_fn = TEMPLATE_REGISTRY[template_id]

    try:
        engine = factory_fn(**request.params)
    except TypeError as te:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid parameters for template '{template_id}': {str(te)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build workflow: {str(e)}")

    try:
        result_ctx = await asyncio.to_thread(engine.run)
    except Exception as e:
        logger.error(f"[/workflow] Runtime error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Workflow execution error: {str(e)}")

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    snapshot = result_ctx.snapshot()

    logger.info(
        f"[/workflow] template='{template_id}' | success={result_ctx.is_successful()} | "
        f"steps={snapshot['history_count']} | duration={duration_ms}ms"
    )

    return WorkflowResponse(
        success=result_ctx.is_successful(),
        template_id=template_id,
        session_id=result_ctx.session_id,
        steps_executed=snapshot["history_count"],
        errors=snapshot["errors"],
        history=snapshot["records"],
        duration_ms=duration_ms,
        timestamp=datetime.datetime.now().isoformat()
    )


@app.get(
    "/workflows",
    dependencies=[Depends(verify_api_key)],
    summary="List available workflow templates",
    tags=["Workflow Templates"]
)
async def list_workflows():
    """Returns all available WORKFLOW_TEMPLATES with parameter documentation."""
    return {
        "templates": [
            {
                "template_id": "enterprise_market_intel",
                "description": "Enterprise market & competitor intelligence (Web search + Site scraping + Structured JSON + Excel + n8n)",
                "required_params": {
                    "search_query": "string - Sector or competitor topic to research"
                },
                "optional_params": {
                    "target_url": "string - URL to scrape (default: https://news.ycombinator.com)",
                    "output_excel": "string - Excel output filename (default: enterprise_market_intel.xlsx)",
                    "output_json": "string - JSON output filename (default: enterprise_market_intel.json)"
                }
            },
            {
                "template_id": "lead_enrichment",
                "description": "Full lead qualification: AI analysis + Excel report + PDF proposal + n8n notification",
                "required_params": {
                    "client_info": "string - Client information to evaluate"
                },
                "optional_params": {
                    "output_excel": "string - Excel filename (default: qualified_leads.xlsx)",
                    "output_pdf": "string - PDF filename (default: client_proposal.pdf)"
                }
            },
            {
                "template_id": "market_research",
                "description": "Market intelligence: web search + site scraping + save report",
                "required_params": {
                    "search_query": "string - Search topic",
                    "target_url": "string - URL to analyze"
                },
                "optional_params": {
                    "output_filename": "string - Report filename"
                }
            },
            {
                "template_id": "duckdb_analytics",
                "description": "Big data analytics: inspect dataset + SQL query + Excel report",
                "required_params": {
                    "file_path": "string - Path to data file (CSV/Parquet/JSON)"
                },
                "optional_params": {
                    "query": "string - Custom SQL query",
                    "output_excel": "string - Output Excel filename"
                }
            }
        ],
        "total": 4,
        "timestamp": datetime.datetime.now().isoformat()
    }


# =============================================================================
# Enterprise Mission Control Demo & Interactive Dashboard Endpoints
# =============================================================================

@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """Serves the interactive Enterprise Mission Control Dashboard UI."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=200,
        content={"message": "Enterprise Agent API Online. Access documentation at /docs."}
    )


@app.get("/api/demo/status", summary="Real-time mission control telemetry", tags=["Demo Dashboard"])
async def get_demo_status():
    """Provides high-density real-time metrics for the Enterprise Mission Control UI."""
    from services.guardrails import guardrails
    from services.tool_registry_bridge import tool_bridge
    from planner import TOOL_CATEGORIES

    # Collect generated artifacts
    valid_exts = {".xlsx", ".pdf", ".json", ".csv", ".txt"}
    artifacts = []
    try:
        for f in os.listdir("."):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts and not f.startswith("."):
                stat = os.stat(f)
                artifacts.append({
                    "name": f,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "download_url": f"/api/demo/download/{f}"
                })
        artifacts.sort(key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        logger.warning(f"Error scanning artifacts: {e}")

    audit_records = list(reversed(guardrails.get_audit_trail()))[:15]

    return {
        "status": "online",
        "version": API_VERSION,
        "tools_total": len(tool_bridge.tools),
        "categories_count": len(TOOL_CATEGORIES),
        "guardrails_mode": guardrails.mode,
        "audit_count": len(guardrails.get_audit_trail()),
        "uptime_sec": round(time.time() - _server_start_time, 1),
        "recent_audits": audit_records,
        "artifacts": artifacts[:12]
    }


class GuardrailsTestRequest(BaseModel):
    action_type: str = Field(..., description="'safe' or 'critical'")
    command: Optional[str] = Field("run_system_code", description="Target tool to verify")


@app.post("/api/demo/guardrails-test", summary="Simulate Guardrails Policy Interception", tags=["Demo Dashboard"])
async def test_guardrails_live(req: GuardrailsTestRequest):
    """
    Simulates a live security policy test on the Guardrails Gateway.
    Shows the client how unauthorized critical code execution is intercepted.
    """
    from services.guardrails import guardrails

    start = time.perf_counter()
    if req.action_type == "safe":
        tool_name = "read_system_file"
        args = {"filename": "README.md"}
    else:
        tool_name = "run_system_code"
        args = {"code": "import shutil; shutil.rmtree('/safe_zone')"}

    allowed, reason = guardrails.verify_action(tool_name, args)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "action_type": req.action_type,
        "tool_tested": tool_name,
        "args": args,
        "allowed": allowed,
        "policy_mode": guardrails.mode,
        "reason": reason,
        "decision_badge": "ALLOWED_SECURE" if allowed else "BLOCKED_BY_GUARDRAILS",
        "duration_ms": duration_ms,
        "audit_logged": True,
        "timestamp": datetime.datetime.now().isoformat()
    }


class ModeChangeRequest(BaseModel):
    mode: str = Field(..., description="Mode: 'auto', 'strict', or 'ask'")


@app.post("/api/demo/set-guardrails-mode", summary="Switch runtime Guardrails policy", tags=["Demo Dashboard"])
async def set_guardrails_mode(req: ModeChangeRequest):
    """Allows dynamic switching of the Guardrails mode during presentations."""
    from services.guardrails import guardrails

    mode = req.mode.lower().strip()
    if mode not in ["auto", "strict", "ask"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Choose 'auto', 'strict', or 'ask'.")

    guardrails.mode = mode
    logger.info(f"[Guardrails] Runtime mode changed to: {mode}")
    return {"success": True, "new_mode": mode}


@app.post("/api/demo/self-healing-test", summary="Demonstrate Reflection Engine Auto-Repair", tags=["Demo Dashboard"])
async def test_self_healing():
    """
    Injects flawed inputs (e.g., malformed URL, missing file extension) and
    demonstrates how the Reflection Engine automatically catches and heals them.
    """
    from services.reflection_engine import reflection_engine

    start = time.perf_counter()
    # Scenario A: Broken URL without protocol
    broken_url_args = {"url": "news.ycombinator.com"}
    fixed_a, corrected_a, reason_a = reflection_engine.reflect_and_correct(
        "scrape_web_page",
        broken_url_args,
        "Error: Invalid URL 'news.ycombinator.com': No scheme supplied."
    )

    # Scenario B: Missing Excel extension
    broken_excel_args = {"filename": "executive_report", "data": [{"KPI": "99.9%"}]}
    fixed_b, corrected_b, reason_b = reflection_engine.reflect_and_correct(
        "generate_excel_report",
        broken_excel_args,
        "Error: Unsupported format. Expected .xlsx extension."
    )

    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "success": True,
        "scenario_a": {
            "name": "URL Scheme Auto-Repair",
            "tool": "scrape_web_page",
            "raw_input": broken_url_args,
            "simulated_error": "No scheme supplied. Missing https://",
            "healed": fixed_a,
            "corrected_input": corrected_a,
            "diagnostic_reason": reason_a
        },
        "scenario_b": {
            "name": "File Extension & Path Auto-Correction",
            "tool": "generate_excel_report",
            "raw_input": broken_excel_args,
            "simulated_error": "Invalid extension. Missing .xlsx",
            "healed": fixed_b,
            "corrected_input": corrected_b,
            "diagnostic_reason": reason_b
        },
        "engine": "ReflectionEngine V2.1 Heuristic + LLM Hybrid",
        "duration_ms": duration_ms,
        "resilience_status": "Zero-Crash Guarantee Active"
    }


@app.get("/api/demo/artifacts", summary="List generated enterprise deliverables", tags=["Demo Dashboard"])
async def list_artifacts():
    """Returns downloadable reports, spreadsheets, dossiers generated by the agent."""
    valid_exts = {".xlsx", ".pdf", ".json", ".csv", ".txt"}
    files = []
    try:
        for f in os.listdir("."):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts and not f.startswith("."):
                stat = os.stat(f)
                files.append({
                    "filename": f,
                    "extension": ext.replace(".", "").upper(),
                    "size_bytes": stat.st_size,
                    "size_formatted": f"{round(stat.st_size / 1024, 1)} KB" if stat.st_size > 1024 else f"{stat.st_size} B",
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "download_url": f"/api/demo/download/{f}"
                })
        files.sort(key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        logger.error(f"Artifacts scan error: {e}")

    return {"count": len(files), "artifacts": files}


@app.get("/api/demo/download/{filename}", summary="Download generated artifact", tags=["Demo Dashboard"])
async def download_artifact(filename: str):
    """Safely serves generated files for direct client download."""
    # Prevent path traversal attacks
    clean_name = os.path.basename(filename)
    if clean_name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename security violation.")

    valid_exts = {".xlsx", ".pdf", ".json", ".csv", ".txt"}
    ext = os.path.splitext(clean_name)[1].lower()
    if ext not in valid_exts:
        raise HTTPException(status_code=403, detail="File extension not permitted for download.")

    file_path = os.path.abspath(clean_name)
    if not os.path.exists(file_path):
        # Check in uploads
        upload_path = os.path.abspath(os.path.join("uploads", clean_name))
        if os.path.exists(upload_path):
            file_path = upload_path
        else:
            raise HTTPException(status_code=404, detail=f"Deliverable '{clean_name}' not found.")

    media_types = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".csv": "text/csv",
        ".txt": "text/plain"
    }

    return FileResponse(
        path=file_path,
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=clean_name
    )


# Mount static directory for assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path),
            "timestamp": datetime.datetime.now().isoformat()
        }
    )


# --- Direct entry point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

