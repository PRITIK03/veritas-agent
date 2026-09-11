const API_BASE = "";
const API_KEY = "local-dev-key-change-me"; // For local demo only; use proper auth flow for deployment

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

tabs.forEach(btn => {
  btn.addEventListener("click", () => {
    tabs.forEach(b => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
    panels.forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const tab = btn.dataset.tab;
    document.querySelector(`.tab-panel[data-tab="${tab}"]`).classList.add("active");
    if (tab === "analytics") loadAnalytics();
  });
});

document.getElementById("submit-btn").addEventListener("click", submitQuery);
document.getElementById("query-input").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitQuery(); }
});

function setLoading(on) {
  document.getElementById("submit-btn").disabled = on;
  document.getElementById("loading").classList.toggle("hidden", !on);
}

async function submitQuery() {
  const input = document.getElementById("query-input");
  const query = input.value.trim();
  if (!query) return;
  setLoading(true);
  hideAnswer();
  try {
    const resp = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
      },
      body: JSON.stringify({ query }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "Request failed");
    renderAnswer(data);
  } catch (err) {
    document.getElementById("error-banner").textContent = err.message || "An error occurred.";
    document.getElementById("error-banner").classList.remove("hidden");
    document.getElementById("answer-panel").classList.remove("hidden");
  } finally {
    setLoading(false);
  }
}

function hideAnswer() {
  ["answer-panel", "error-banner"].forEach(id => document.getElementById(id).classList.add("hidden"));
}

function renderAnswer(d) {
  const panel = document.getElementById("answer-panel");
  panel.classList.remove("hidden");

  const badge = document.getElementById("verdict-badge");
  badge.className = "badge";
  if (d.failure_reason) {
    badge.classList.add("error");
    badge.textContent = "ERROR";
  } else if (d.grounded) {
    badge.classList.add("grounded");
    badge.textContent = "GROUNDED";
  } else {
    badge.classList.add("unverified");
    badge.textContent = "UNVERIFIED";
  }

  document.getElementById("route-label").textContent = d.route || "—";
  document.getElementById("answer-text").textContent = d.answer || "";

  const srcSection = document.getElementById("sources-section");
  const srcList = document.getElementById("sources-list");
  if (d.sources && d.sources.length > 0) {
    srcSection.classList.remove("hidden");
    srcList.innerHTML = d.sources.map(s => `<li>${s.file || "unknown"} (chunk ${s.chunk_id ?? "?"})</li>`).join("");
  } else {
    srcSection.classList.add("hidden");
  }

  const stats = document.getElementById("run-stats");
  stats.classList.remove("hidden");
  document.getElementById("stat-latency").textContent = (d.latency_ms ?? "—") + " ms";
  document.getElementById("stat-input-tokens").textContent = d.input_tokens ?? "—";
  document.getElementById("stat-output-tokens").textContent = d.output_tokens ?? "—";
  document.getElementById("stat-cost").textContent = "$" + (d.estimated_cost_usd ?? "0.00");
}

async function loadAnalytics() {
  const loading = document.getElementById("analytics-loading");
  const empty = document.getElementById("analytics-empty");
  const body = document.getElementById("analytics-body");
  loading.classList.remove("hidden");
  empty.classList.add("hidden");
  body.classList.add("hidden");

  try {
    const resp = await fetch(`${API_BASE}/analytics`, {
      headers: { "X-API-Key": API_KEY },
    });
    const data = await resp.json();
    loading.classList.add("hidden");
    body.classList.remove("hidden");

    document.getElementById("a-total").textContent = data.total_queries ?? 0;
    document.getElementById("a-session").textContent = data.queries_this_session ?? 0;
    document.getElementById("a-latency").textContent = (data.avg_latency_ms ?? 0).toFixed(0) + "ms";
    document.getElementById("a-cost").textContent = "$" + (data.avg_estimated_cost_usd ?? 0).toFixed(4);
    document.getElementById("a-total-cost").textContent = "$" + (data.total_estimated_cost_usd ?? 0).toFixed(4);

    const rate = data.grounding_success_rate_pct ?? 0;
    document.getElementById("a-rate-pct").textContent = rate.toFixed(0) + "%";
    document.getElementById("a-progress-bar").style.width = rate + "%";

    const total = (data.route_counts?.rag || 0) + (data.route_counts?.web_search || 0) || 1;
    const ragPct = ((data.route_counts?.rag || 0) / total) * 100;
    const webPct = ((data.route_counts?.web_search || 0) / total) * 100;
    document.getElementById("a-rag-bar").style.width = ragPct + "%";
    document.getElementById("a-rag-val").textContent = data.route_counts?.rag ?? 0;
    document.getElementById("a-web-bar").style.width = webPct + "%";
    document.getElementById("a-web-val").textContent = data.route_counts?.web_search ?? 0;
  } catch (err) {
    loading.classList.add("hidden");
    empty.classList.remove("hidden");
    empty.textContent = err.message || "Failed to load analytics.";
  }
}
