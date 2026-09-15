const API_BASE = "";
const API_KEY = "local-dev-key-change-me";

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
let trendChart = null;

/* ── Tab switching ── */
tabs.forEach(btn => {
  btn.addEventListener("click", () => {
    tabs.forEach(b => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
    panels.forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const tab = btn.dataset.tab;
    document.querySelector(`.tab-panel[data-tab="${tab}"]`).classList.add("active");
    if (tab === "analytics") loadAnalytics();
    if (tab === "history") loadHistory();
  });
});

/* ── Theme toggle ── */
function initTheme() {
  const saved = localStorage.getItem("veritas-theme");
  if (saved === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  }
}

document.getElementById("theme-toggle").addEventListener("click", () => {
  const html = document.documentElement;
  const isDark = html.getAttribute("data-theme") === "dark";
  if (isDark) {
    html.removeAttribute("data-theme");
    localStorage.setItem("veritas-theme", "light");
  } else {
    html.setAttribute("data-theme", "dark");
    localStorage.setItem("veritas-theme", "dark");
  }
});

initTheme();

/* ── Query submission ── */
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
    animateFlow(data);
    document.getElementById("answer-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    document.getElementById("error-banner").textContent = err.message || "An error occurred.";
    document.getElementById("error-banner").classList.remove("hidden");
    document.getElementById("answer-panel").classList.remove("hidden");
  } finally {
    setLoading(false);
  }
}

function hideAnswer() {
  ["answer-panel", "error-banner", "flow-panel"].forEach(id => document.getElementById(id).classList.add("hidden"));
  resetFlow();
}

/* ── Execution flow diagram ── */
const FLOW_STEPS = ["router", "specialist", "grounding", "answer"];

function resetFlow() {
  document.querySelectorAll(".flow-node").forEach(n => n.classList.remove("active"));
  document.querySelectorAll(".flow-edge").forEach(e => e.classList.remove("active"));
  document.getElementById("retry-edge").classList.add("hidden");
  document.querySelector(".flow-node[data-node='retry']").classList.add("hidden");
}

function animateFlow(data) {
  resetFlow();
  const flowPanel = document.getElementById("flow-panel");
  flowPanel.classList.remove("hidden");

  const route = data.route || "rag";
  const retryCount = data.retry_count ?? 0;
  const grounded = data.grounded;
  const hasRetry = retryCount > 0;

  document.getElementById("flow-route").textContent = `Route: ${route}`;
  document.getElementById("flow-retry").textContent = `Retry: ${retryCount}`;

  const delay = 350;

  function activateNode(name, index) {
    setTimeout(() => {
      const node = document.querySelector(`.flow-node[data-node="${name}"]`);
      if (node) node.classList.add("active");
      const edges = document.querySelectorAll(".flow-edge");
      if (index > 0 && edges[index - 1]) edges[index - 1].classList.add("active");
    }, index * delay);
  }

  activateNode("router", 0);
  activateNode("specialist", 1);
  activateNode("grounding", 2);

  if (hasRetry) {
    setTimeout(() => {
      document.getElementById("retry-edge").classList.remove("hidden");
      document.querySelector(".flow-node[data-node='retry']").classList.remove("hidden");
      document.querySelector(".flow-node[data-node='retry']").classList.add("active");
    }, 3 * delay);
    activateNode("specialist", 4);
    activateNode("grounding", 5);
    activateNode("answer", 6);
  } else {
    activateNode("answer", 3);
  }
}

/* ── Answer rendering ── */
function renderAnswer(d) {
  const panel = document.getElementById("answer-panel");
  panel.classList.remove("hidden");
  panel.style.animation = "none";
  panel.offsetHeight; // reflow
  panel.style.animation = "";

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

  const copyAnswer = document.getElementById("copy-answer");
  copyAnswer.textContent = "Copy";
  copyAnswer.onclick = () => copyToClipboard(d.answer || "", copyAnswer);

  const srcSection = document.getElementById("sources-section");
  const srcList = document.getElementById("sources-list");
  if (d.sources && d.sources.length > 0) {
    srcSection.classList.remove("hidden");
    srcList.innerHTML = d.sources.map((s, i) => {
      const text = `${s.file || "unknown"} (chunk ${s.chunk_id ?? "?"})`;
      return `<li><span>${text}</span><button class="source-copy" data-idx="${i}">Copy</button></li>`;
    }).join("");
    srcList.querySelectorAll(".source-copy").forEach(btn => {
      const text = d.sources[btn.dataset.idx];
      const label = `${text.file || "unknown"} (chunk ${text.chunk_id ?? "?"})`;
      btn.addEventListener("click", () => copyToClipboard(label, btn));
    });
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

async function copyToClipboard(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    const old = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => btn.textContent = old, 1500);
  } catch (e) {
    btn.textContent = "Copy failed";
    setTimeout(() => btn.textContent = "Copy", 1500);
  }
}

/* ── History ── */
async function loadHistory() {
  const loading = document.getElementById("history-loading");
  const empty = document.getElementById("history-empty");
  const body = document.getElementById("history-body");
  loading.classList.remove("hidden");
  empty.classList.add("hidden");
  body.classList.add("hidden");

  try {
    const resp = await fetch(`${API_BASE}/analytics/recent`, {
      headers: { "X-API-Key": API_KEY },
    });
    const data = await resp.json();
    loading.classList.add("hidden");
    if (!data.length) {
      empty.classList.remove("hidden");
      return;
    }
    body.classList.remove("hidden");
    renderHistory(data);
  } catch (err) {
    loading.classList.add("hidden");
    empty.classList.remove("hidden");
    empty.textContent = err.message || "Failed to load history.";
  }
}

function renderHistory(rows) {
  const container = document.getElementById("history-table");
  container.innerHTML = rows.map((row, idx) => {
    const ts = new Date(row.created_at).toLocaleString();
    const cost = "$" + (row.estimated_cost_usd ?? 0).toFixed(6);
    const badgeClass = row.grounded ? "grounded" : (row.failure_reason ? "error" : "unverified");
    const badgeText = row.grounded ? "Grounded" : (row.failure_reason ? "Error" : "Unverified");
    return `
      <div class="history-row" data-idx="${idx}">
        <div class="history-main">
          <div class="history-query" title="${escapeHtml(row.query)}">${escapeHtml(row.query)}</div>
          <div class="history-route">${row.route}</div>
          <div class="history-cost">${cost}</div>
          <div class="history-latency">${row.latency_ms}ms</div>
        </div>
        <div class="history-detail">
          <time>${ts}</time>
          <span class="badge ${badgeClass}">${badgeText}</span>
          ${row.failure_reason ? `<p class="fail-reason">${escapeHtml(row.failure_reason)}</p>` : ""}
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".history-row").forEach(row => {
    row.addEventListener("click", () => row.classList.toggle("expanded"));
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ── Analytics ── */
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

    animateValue("a-total", data.total_queries ?? 0, 0, 800, v => Math.round(v));
    animateValue("a-session", data.queries_this_session ?? 0, 0, 800, v => Math.round(v));
    animateValue("a-latency", data.avg_latency_ms ?? 0, 0, 800, v => Math.round(v) + "ms");
    animateValue("a-cost", data.avg_estimated_cost_usd ?? 0, 0, 800, v => "$" + v.toFixed(4));
    animateValue("a-total-cost", data.total_estimated_cost_usd ?? 0, 0, 800, v => "$" + v.toFixed(4));

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

    loadTrendChart();
  } catch (err) {
    loading.classList.add("hidden");
    empty.classList.remove("hidden");
    empty.textContent = err.message || "Failed to load analytics.";
  }
}

function animateValue(id, end, start, duration, formatter) {
  const el = document.getElementById(id);
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / duration, 1);
    const val = start + (end - start) * easeOutQuad(t);
    el.textContent = formatter(val);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function easeOutQuad(t) { return t * (2 - t); }

/* ── Trend chart ── */
async function loadTrendChart() {
  try {
    const resp = await fetch(`${API_BASE}/analytics/trend`, {
      headers: { "X-API-Key": API_KEY },
    });
    const data = await resp.json();
    renderTrendChart(data);
  } catch (err) {
    console.error("Failed to load trend", err);
  }
}

function renderTrendChart(data) {
  const ctx = document.getElementById("trend-chart").getContext("2d");
  const labels = data.map((_, i) => `#${i + 1}`);
  const costs = data.map(d => d.estimated_cost_usd);
  const pointColors = data.map(d => d.grounded ? "#0F766E" : "#C2410C");

  if (trendChart) {
    trendChart.destroy();
  }

  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const gridColor = isDark ? "#333333" : "#E7E5E4";
  const textColor = isDark ? "#A0A0A0" : "#78716C";

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Cost per query ($)",
        data: costs,
        borderColor: "#0F766E",
        backgroundColor: "rgba(15, 118, 110, 0.08)",
        pointBackgroundColor: pointColors,
        pointBorderColor: pointColors,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `$${ctx.parsed.y.toFixed(6)} · ${data[ctx.dataIndex].grounded ? "Grounded" : "Not grounded"}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: gridColor, drawBorder: false },
          ticks: { color: textColor, font: { size: 10, family: "'JetBrains Mono', monospace" } },
        },
        y: {
          grid: { color: gridColor, drawBorder: false },
          ticks: {
            color: textColor,
            font: { size: 10, family: "'JetBrains Mono', monospace" },
            callback: v => "$" + v.toFixed(5),
          },
        },
      },
    },
  });
}
