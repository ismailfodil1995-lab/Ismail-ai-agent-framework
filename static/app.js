// =============================================================================
// Ismail Smart Agent V2.1 — Mission Control Interactive Logic
// =============================================================================

const API_KEY = "ismail-agent-secret-key-2026";

function getHeaders() {
  return {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
  };
}

// Log message to live terminal dock
function logTerminal(badge, type, msg) {
  const body = document.getElementById("terminalLogBody");
  if (!body) return;

  const now = new Date();
  const timeStr = `[${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}]`;

  const line = document.createElement("div");
  line.className = "terminal-line";

  let badgeClass = "term-badge-info";
  if (type === "ok") badgeClass = "term-badge-ok";
  if (type === "dag") badgeClass = "term-badge-dag";
  if (type === "guard") badgeClass = "term-badge-guard";
  if (type === "reflect") badgeClass = "term-badge-reflect";

  line.innerHTML = `
    <span class="term-time">${timeStr}</span>
    <span class="${badgeClass}">${badge}</span>
    <span class="term-msg">${msg}</span>
  `;

  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function clearTerminal() {
  const body = document.getElementById("terminalLogBody");
  if (body) body.innerHTML = "";
}

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-tab-btn").forEach(el => el.classList.remove("active"));

  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  const btn = Array.from(document.querySelectorAll(".nav-tab-btn")).find(b => 
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(tabId)
  );
  if (btn) btn.classList.add("active");
}

// Fetch Real-time Telemetry
async function fetchTelemetry() {
  try {
    const res = await fetch("/api/demo/status");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("headerToolsStatus").textContent = `${data.tools_total} Tools Verified Active`;
    document.getElementById("cardToolsCount").textContent = `${data.tools_total} Tools`;
    document.getElementById("cardGuardrailsMode").textContent = `Mode: ${data.guardrails_mode.toUpperCase()}`;
    document.getElementById("cardAuditCount").textContent = `${data.audit_count} Audits Logged`;

    const select = document.getElementById("guardrailsModeSelect");
    if (select && select.value !== data.guardrails_mode) {
      select.value = data.guardrails_mode;
    }

    if (data.artifacts) {
      document.getElementById("vaultBadgeCount").textContent = data.artifacts.length;
      renderArtifacts(data.artifacts);
    }
  } catch (err) {
    console.warn("Telemetry fetch error:", err);
  }
}

// Change Guardrails Mode
async function changeGuardrailsMode(mode) {
  try {
    logTerminal("[GUARDRAILS_MODE]", "guard", `Changing Guardrails policy mode to: ${mode.toUpperCase()}`);
    const res = await fetch("/api/demo/set-guardrails-mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[GUARDRAILS_MODE]", "ok", `Active security policy is now: ${data.new_mode.toUpperCase()}`);
      fetchTelemetry();
    }
  } catch (err) {
    logTerminal("[GUARDRAILS_ERROR]", "guard", `Failed to set mode: ${err}`);
  }
}

// TAB 1: Run Enterprise Market Intel DAG
async function runMarketIntelDAG() {
  const btn = document.getElementById("btnRunMarketDag");
  const query = document.getElementById("inputDagQuery").value.trim();
  const targetUrl = document.getElementById("inputDagUrl").value.trim();
  const excelName = document.getElementById("inputDagExcel").value.trim();
  const viewer = document.getElementById("dagOutputViewer");
  const dlBtn = document.getElementById("btnDownloadExcelDag");
  const timeBadge = document.getElementById("dagOverallTime");

  if (!query) {
    alert("Please enter a search topic or competitor query.");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Executing Autonomous DAG...`;
  dlBtn.style.display = "none";
  viewer.textContent = "Autonomous DAG Pipeline initiated...\nTopological sorting validated.\nExecuting nodes asynchronously...";

  // Reset node cards to Pending
  const nodes = ["intel_search", "content_scrape", "json_structuring", "excel_export", "n8n_dispatch"];
  nodes.forEach(id => {
    const card = document.getElementById(`nodeCard-${id}`);
    const icon = document.getElementById(`icon-${id}`);
    const time = document.getElementById(`time-${id}`);
    if (card) { card.className = "dag-node-card pending"; }
    if (icon) { icon.textContent = "⚪"; }
    if (time) { time.textContent = "Pending"; }
  });

  logTerminal("[DAG_START]", "dag", `Launching Enterprise Market Intel DAG for topic: "${query}"`);

  // Progressive node visual updates
  let currentStep = 0;
  const nodeInterval = setInterval(() => {
    if (currentStep < nodes.length) {
      const activeId = nodes[currentStep];
      const card = document.getElementById(`nodeCard-${activeId}`);
      const icon = document.getElementById(`icon-${activeId}`);
      const time = document.getElementById(`time-${activeId}`);
      if (card) card.className = "dag-node-card running";
      if (icon) icon.textContent = "🟡";
      if (time) time.textContent = "Running...";
      logTerminal("[DAG_NODE]", "dag", `Executing node: ${activeId}`);
      currentStep++;
    }
  }, 400);

  const startMs = performance.now();

  try {
    const res = await fetch("/workflow", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        template_id: "enterprise_market_intel",
        params: {
          search_query: query,
          target_url: targetUrl || "https://news.ycombinator.com",
          output_excel: excelName || "enterprise_market_intel.xlsx"
        }
      })
    });

    clearInterval(nodeInterval);
    const duration = Math.round(performance.now() - startMs);
    timeBadge.textContent = `Completed in ${duration}ms`;

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`API error (${res.status}): ${errText}`);
    }

    const data = await res.json();

    // Mark all nodes as success with timing breakdown
    nodes.forEach((id, idx) => {
      const card = document.getElementById(`nodeCard-${id}`);
      const icon = document.getElementById(`icon-${id}`);
      const time = document.getElementById(`time-${id}`);
      if (card) card.className = "dag-node-card success";
      if (icon) icon.textContent = "✅";
      if (time) time.textContent = `${Math.round(duration / nodes.length)}ms`;
    });

    logTerminal("[DAG_SUCCESS]", "ok", `DAG Pipeline completed successfully in ${duration}ms. 5/5 nodes resolved.`);

    // Display formatted output
    viewer.textContent = JSON.stringify(data, null, 2);

    // Show Excel download button
    dlBtn.style.display = "inline-flex";
    dlBtn.href = `/api/demo/download/${excelName || "enterprise_market_intel.xlsx"}`;

    fetchTelemetry();
  } catch (err) {
    clearInterval(nodeInterval);
    timeBadge.textContent = "Execution Failed";
    viewer.textContent = `Error executing DAG: ${err.message}`;
    logTerminal("[DAG_ERROR]", "guard", `Execution failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>🚀</span> Launch Autonomous Pipeline`;
  }
}

// TAB 2: Test Guardrails Security
async function testGuardrails(actionType) {
  const viewer = document.getElementById("guardrailsTestOutput");
  viewer.textContent = `Testing Guardrails Gateway with '${actionType}' action...`;

  logTerminal("[GUARDRAILS_CHECK]", "guard", `Simulating ${actionType.toUpperCase()} action verification...`);

  try {
    const res = await fetch("/api/demo/guardrails-test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_type: actionType })
    });

    const data = await res.json();
    viewer.textContent = JSON.stringify(data, null, 2);

    if (data.allowed) {
      logTerminal("[GUARDRAILS_DECISION]", "ok", `Access GRANTED for tool '${data.tool_tested}' under '${data.policy_mode}' policy.`);
    } else {
      logTerminal("[GUARDRAILS_DECISION]", "guard", `SECURITY SHIELD TRIGGERED: Action '${data.tool_tested}' BLOCKED. Reason: ${data.reason}`);
    }

    fetchTelemetry();
  } catch (err) {
    viewer.textContent = `Guardrails test error: ${err.message}`;
  }
}

// TAB 2: Test Reflection Self-Healing
async function testSelfHealing() {
  const viewer = document.getElementById("selfHealingOutput");
  viewer.textContent = "Injecting flawed parameters (unprefixed URL & missing .xlsx extension)...";

  logTerminal("[REFLECTION_START]", "reflect", "Triggering intentional flaw injection for Self-Healing demonstration...");

  try {
    const res = await fetch("/api/demo/self-healing-test", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });

    const data = await res.json();
    viewer.textContent = JSON.stringify(data, null, 2);

    logTerminal("[REFLECTION_HEAL]", "ok", `Scenario A Healed: ${data.scenario_a.corrected_input.url} (${data.scenario_a.diagnostic_reason})`);
    logTerminal("[REFLECTION_HEAL]", "ok", `Scenario B Healed: ${data.scenario_b.corrected_input.filename} (${data.scenario_b.diagnostic_reason})`);
  } catch (err) {
    viewer.textContent = `Reflection test error: ${err.message}`;
  }
}

// TAB 3: Run Custom Natural Language Prompt
async function runCustomPrompt() {
  const input = document.getElementById("customPromptInput").value.trim();
  const parallel = document.getElementById("checkParallelExecution").checked;
  const viewer = document.getElementById("promptResultViewer");

  if (!input) {
    alert("Please enter a command.");
    return;
  }

  viewer.textContent = "Planner analyzing intent & applying Sparse Tool Loading...";
  logTerminal("[PLANNER_START]", "info", `Analyzing query: "${input.substring(0, 50)}..."`);

  try {
    const res = await fetch("/run", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        query: input,
        parallel: parallel
      })
    });

    const data = await res.json();
    viewer.textContent = JSON.stringify(data, null, 2);

    logTerminal("[EXECUTOR_DONE]", data.success ? "ok" : "guard", `Prompt executed in ${data.duration_ms}ms. Success: ${data.success}`);
    fetchTelemetry();
  } catch (err) {
    viewer.textContent = `Execution error: ${err.message}`;
    logTerminal("[EXECUTOR_ERROR]", "guard", `Error: ${err.message}`);
  }
}

// TAB 4: Render Deliverables Vault
function renderArtifacts(artifacts) {
  const grid = document.getElementById("vaultGridContainer");
  if (!grid) return;

  grid.innerHTML = "";

  if (!artifacts || artifacts.length === 0) {
    grid.innerHTML = `<div style="color:var(--text-muted); font-size:0.9rem; grid-column:1/-1;">No deliverables found. Run a DAG workflow or analytical pipeline to generate workbooks and reports.</div>`;
    return;
  }

  artifacts.forEach(item => {
    const ext = item.name.split('.').pop().toLowerCase();
    const extClass = `ext-${ext}` in { 'ext-xlsx': 1, 'ext-pdf': 1, 'ext-json': 1, 'ext-txt': 1 } ? `ext-${ext}` : 'ext-txt';

    const card = document.createElement("div");
    card.className = "vault-card";
    card.innerHTML = `
      <div class="vault-info">
        <span class="vault-ext-badge ${extClass}">${ext.toUpperCase()}</span>
        <div class="vault-meta">
          <span class="vault-filename" title="${item.name}">${item.name}</span>
          <span class="vault-submeta">${item.size_kb} KB • ${item.modified}</span>
        </div>
      </div>
      <a href="${item.download_url}" class="vault-dl-btn" download>Download ⬇</a>
    `;
    grid.appendChild(card);
  });
}

async function refreshArtifacts() {
  logTerminal("[VAULT_REFRESH]", "info", "Scanning local filesystem for newly generated deliverables...");
  await fetchTelemetry();
}

// Initial Boot
document.addEventListener("DOMContentLoaded", () => {
  fetchTelemetry();
  // Poll telemetry every 10 seconds
  setInterval(fetchTelemetry, 10000);
});
