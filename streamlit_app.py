"""
Veritas Agent — UI
Evidence-first, verification-forward. Light mode, serif+mono, case-file layout.
Talks to the FastAPI backend only — no direct pipeline imports.
"""

import requests
import streamlit as st
import json

API_URL = "http://localhost:8000/query"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Veritas Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Fonts + global CSS ─────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500&display=swap" rel="stylesheet">

<style>
/* ── Base palette ── */
:root {
    --paper:      #F7F5F0;
    --paper-dark: #EDEAE2;
    --ink:        #1C1B18;
    --ink-mid:    #4A4843;
    --ink-faint:  #9A9690;
    --verified:   #3D7A5A;
    --verified-bg:#EAF4EE;
    --flagged:    #A04030;
    --flagged-bg: #F8EDEA;
    --accent:     #5B4FCF;
    --accent-soft:#EEEAFF;
    --border:     #DDD9D0;
    --mono:       'JetBrains Mono', monospace;
    --serif:      'Lora', serif;
    --sans:       'Inter', sans-serif;
}

/* ── Full app background ── */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--paper) !important;
    color: var(--ink) !important;
}
[data-testid="stSidebar"] {
    background-color: var(--paper-dark) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Typography overrides ── */
h1, h2, h3 {
    font-family: var(--serif) !important;
    color: var(--ink) !important;
}
p, li, label, div { font-family: var(--sans) !important; color: var(--ink) !important; }
code, pre, .stCode { font-family: var(--mono) !important; }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #fff !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    color: var(--ink) !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(91,79,207,0.10) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--ink) !important;
    color: var(--paper) !important;
    font-family: var(--sans) !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
    letter-spacing: 0.02em !important;
    transition: background 0.15s ease !important;
}
.stButton > button:hover { background: #3B3A35 !important; }

/* ── Verdict stamp ── */
@keyframes stamp {
    0%   { transform: scale(1.08); opacity: 0; }
    60%  { transform: scale(0.97); opacity: 1; }
    100% { transform: scale(1.00); opacity: 1; }
}
.verdict-stamp {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 1.1rem;
    border-radius: 4px;
    font-family: var(--mono) !important;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: 2px solid;
    animation: stamp 0.35s cubic-bezier(0.22,1,0.36,1) both;
}
.verdict-verified {
    color: var(--verified);
    background: var(--verified-bg);
    border-color: var(--verified);
}
.verdict-flagged {
    color: var(--flagged);
    background: var(--flagged-bg);
    border-color: var(--flagged);
}

/* ── Answer block ── */
.answer-block {
    background: #fff;
    border: 1px solid var(--border);
    border-left: 4px solid var(--ink);
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    font-family: var(--sans) !important;
    font-size: 1.0rem;
    line-height: 1.75;
    color: var(--ink);
    margin: 0.8rem 0 1.2rem;
}

/* ── Citation pill ── */
.cite-pill {
    display: inline-block;
    background: var(--paper-dark);
    border: 1px solid var(--border);
    border-radius: 3px;
    font-family: var(--mono) !important;
    font-size: 0.7rem;
    padding: 1px 6px;
    color: var(--ink-mid);
    vertical-align: middle;
    margin: 0 2px;
}

/* ── Source card ── */
.source-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    position: relative;
}
.source-card .src-num {
    font-family: var(--mono) !important;
    font-size: 0.72rem;
    color: var(--ink-faint);
    margin-bottom: 0.3rem;
}
.source-card .src-label {
    font-family: var(--mono) !important;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--ink-mid);
    word-break: break-all;
}

/* ── Trace step ── */
.trace-step {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid var(--border);
}
.trace-step:last-child { border-bottom: none; }
.trace-icon {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: var(--paper-dark);
    border: 1.5px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.trace-body { flex: 1; }
.trace-label {
    font-family: var(--mono) !important;
    font-size: 0.72rem;
    color: var(--ink-faint);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 2px;
}
.trace-value {
    font-family: var(--sans) !important;
    font-size: 0.88rem;
    color: var(--ink);
}

/* ── Metric card ── */
.metric-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.2rem;
    text-align: center;
}
.metric-value {
    font-family: var(--mono) !important;
    font-size: 1.6rem;
    font-weight: 500;
    color: var(--ink);
    line-height: 1.2;
}
.metric-label {
    font-family: var(--sans) !important;
    font-size: 0.75rem;
    color: var(--ink-faint);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Ledger row ── */
.ledger-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 0.8rem;
    border-radius: 5px;
    background: #fff;
    border: 1px solid var(--border);
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color 0.12s;
}
.ledger-row:hover { border-color: var(--accent); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--sans) !important;
    font-size: 0.87rem !important;
    color: var(--ink-mid) !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    padding: 0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    border-bottom: 2px solid var(--ink) !important;
    font-weight: 600 !important;
}

/* ── Misc ── */
hr { border-color: var(--border) !important; }
.stExpander { border: 1px solid var(--border) !important; border-radius: 6px !important; }
[data-testid="stMetricValue"] { font-family: var(--mono) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Helper renderers
# ══════════════════════════════════════════════════════════════════════════════

def verdict_stamp(grounded: bool) -> str:
    if grounded:
        return '<span class="verdict-stamp verdict-verified">✦ Verified</span>'
    return '<span class="verdict-stamp verdict-flagged">⚑ Not grounded</span>'


def route_badge(route: str) -> str:
    icon = "📚" if route == "rag" else "🌐"
    label = "Knowledge Base" if route == "rag" else "Web Search"
    return f'<span class="cite-pill">{icon} {label}</span>'


def render_source_card(idx: int, src: dict):
    if "url" in src:
        label = src.get("title") or src.get("url", "")
        detail = f'<a href="{src["url"]}" target="_blank" style="color:var(--accent);font-size:0.75rem;">{src["url"]}</a>'
    else:
        label = src.get("file", "unknown")
        detail = f'chunk #{src.get("chunk_id", "?")}'
    st.markdown(f"""
    <div class="source-card">
        <div class="src-num">Source [{idx}]</div>
        <div class="src-label">{label}</div>
        <div style="font-family:var(--mono);font-size:0.75rem;color:var(--ink-faint);margin-top:3px">{detail}</div>
    </div>""", unsafe_allow_html=True)


def render_trace(data: dict):
    route_label = "Knowledge Base (RAG)" if data["route"] == "rag" else "Web Search (Tavily)"
    grounded_label = "✦ Grounded — answer is supported by retrieved evidence" \
        if data["grounded"] else "⚑ Not grounded — answer may not be supported"
    steps = [
        ("🔀", "Router decision", route_label),
        ("⚙️", "Specialist used", route_label),
        ("🔬", "Grounding check", grounded_label),
        ("⏱", "Latency", f"{data['latency_ms']} ms"),
        ("🔢", "Tokens", f"in={data['input_tokens']}  out={data['output_tokens']}"),
        ("💰", "Est. cost", f"${data['estimated_cost_usd']:.6f}"),
    ]
    for icon, label, value in steps:
        st.markdown(f"""
        <div class="trace-step">
            <div class="trace-icon">{icon}</div>
            <div class="trace-body">
                <div class="trace-label">{label}</div>
                <div class="trace-value">{value}</div>
            </div>
        </div>""", unsafe_allow_html=True)


def routing_split_svg(rag: int, web: int) -> str:
    """Segmented ratio bar — hand-rolled SVG, no library."""
    total = rag + web or 1
    rag_pct = rag / total
    web_pct = web / total
    W, H = 260, 24
    rag_w = int(W * rag_pct)
    web_w = W - rag_w
    return f"""
    <svg width="{W}" height="{H+28}" xmlns="http://www.w3.org/2000/svg"
         style="display:block;margin:0 auto">
      <rect x="0" y="0" width="{rag_w}" height="{H}"
            rx="4" ry="0" fill="#3D7A5A" opacity="0.85"/>
      <rect x="{rag_w}" y="0" width="{web_w}" height="{H}"
            rx="0" ry="4" fill="#5B4FCF" opacity="0.75"/>
      <!-- left label -->
      <text x="6" y="{H+16}" font-family="JetBrains Mono,monospace"
            font-size="10" fill="#3D7A5A">📚 RAG {rag_pct*100:.0f}%</text>
      <!-- right label -->
      <text x="{W}" y="{H+16}" font-family="JetBrains Mono,monospace"
            font-size="10" fill="#5B4FCF" text-anchor="end">🌐 Web {web_pct*100:.0f}%</text>
    </svg>"""


def grounding_sparkline_svg(trend: list) -> str:
    """Grounding rate sparkline over recent N queries — hand-rolled SVG."""
    if not trend:
        return "<p style='font-family:var(--mono);font-size:0.8rem;color:var(--ink-faint)'>No data yet.</p>"
    W, H, PAD = 260, 52, 6
    n = len(trend)
    # rolling 5-query grounding rate at each point
    rates = []
    for i in range(n):
        window = trend[max(0, i-4):i+1]
        rates.append(sum(1 for _, g in window if g) / len(window))
    min_r, max_r = 0.0, 1.0
    def x(i): return PAD + (i / max(n-1, 1)) * (W - 2*PAD)
    def y(v): return PAD + (1 - v) * (H - 2*PAD)
    pts = " ".join(f"{x(i):.1f},{y(r):.1f}" for i, r in enumerate(rates))
    # fill area
    fill_pts = f"{x(0):.1f},{y(0):.1f} {pts} {x(n-1):.1f},{H}"
    last_x, last_y = x(n-1), y(rates[-1])
    last_val = rates[-1]
    label_color = "#3D7A5A" if last_val >= 0.5 else "#A04030"
    return f"""
    <svg width="{W}" height="{H+20}" xmlns="http://www.w3.org/2000/svg"
         style="display:block;margin:0 auto">
      <!-- grid lines -->
      <line x1="{PAD}" y1="{y(1.0):.1f}" x2="{W-PAD}" y2="{y(1.0):.1f}"
            stroke="#DDD9D0" stroke-width="1" stroke-dasharray="3,3"/>
      <line x1="{PAD}" y1="{y(0.5):.1f}" x2="{W-PAD}" y2="{y(0.5):.1f}"
            stroke="#DDD9D0" stroke-width="1" stroke-dasharray="3,3"/>
      <!-- fill -->
      <polygon points="{fill_pts} {x(0):.1f},{H}"
               fill="#3D7A5A" opacity="0.08"/>
      <!-- line -->
      <polyline points="{pts}" fill="none"
                stroke="#3D7A5A" stroke-width="2"
                stroke-linejoin="round" stroke-linecap="round"/>
      <!-- last point dot -->
      <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="4"
              fill="{label_color}" stroke="#fff" stroke-width="1.5"/>
      <!-- axis labels -->
      <text x="{PAD}" y="{H+14}" font-family="JetBrains Mono,monospace"
            font-size="9" fill="#9A9690">older</text>
      <text x="{W-PAD}" y="{H+14}" font-family="JetBrains Mono,monospace"
            font-size="9" fill="#9A9690" text-anchor="end">latest</text>
      <text x="{W-PAD}" y="{y(1.0)+4:.1f}" font-family="JetBrains Mono,monospace"
            font-size="9" fill="#9A9690" text-anchor="end">100%</text>
      <text x="{W-PAD}" y="{y(0.5)+4:.1f}" font-family="JetBrains Mono,monospace"
            font-size="9" fill="#9A9690" text-anchor="end">50%</text>
    </svg>"""


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding:0.2rem 0 1.2rem">
        <div style="font-family:'Lora',serif;font-size:1.5rem;font-weight:700;
                    color:#1C1B18;letter-spacing:-0.01em">⚖️ Veritas</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                    color:#9A9690;letter-spacing:0.08em;text-transform:uppercase;
                    margin-top:2px">Evidence · Verification · Accuracy</div>
    </div>
    <hr style="border-color:#DDD9D0;margin-bottom:1.2rem">
    """, unsafe_allow_html=True)

    nav = st.radio(
        "",
        ["📋  Query", "📊  Dashboard", "📜  Ledger"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # live analytics in sidebar
    try:
        from app.db import get_analytics_summary, get_grounding_trend
        summary = get_analytics_summary()
        trend   = get_grounding_trend(30)

        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                    color:#9A9690;text-transform:uppercase;letter-spacing:0.06em;
                    margin-bottom:0.6rem">Live stats</div>""",
        unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Queries", summary["total_queries"])
        with c2:
            st.metric("Grounded", f"{summary['grounding_success_rate_pct']:.0f}%")

        st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)
        st.markdown(grounding_sparkline_svg(trend), unsafe_allow_html=True)
        st.caption("Grounding rate — rolling 5-query window")

    except Exception:
        st.caption("Connect Postgres to see live stats.")

    st.markdown("<hr style='border-color:#DDD9D0;margin-top:1.5rem'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;
                color:#9A9690;line-height:1.8">
    API: <code>localhost:8000</code><br>
    Model: <code>gemini-3.6-flash</code><br>
    Cache: <code>data/llm_cache.json</code>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Page: Query
# ══════════════════════════════════════════════════════════════════════════════

if "Query" in nav:
    st.markdown("""
    <h1 style="font-family:'Lora',serif;font-size:2rem;font-weight:700;
               margin-bottom:0.2rem">Ask Veritas</h1>
    <p style="color:#9A9690;font-size:0.9rem;margin-bottom:1.8rem">
    Answers are grounded against retrieved evidence before being returned.
    Every response shows its sources and whether it can be verified.
    </p>""", unsafe_allow_html=True)

    query = st.text_area(
        "Your query",
        placeholder="e.g. What are the storage limits on the paid pricing tiers?",
        height=80,
        label_visibility="collapsed",
    )

    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        submitted = st.button("Submit →", use_container_width=True)
    with col_hint:
        st.markdown("""
        <p style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                  color:#9A9690;margin-top:0.5rem">
        Routes to knowledge base or web search automatically.
        </p>""", unsafe_allow_html=True)

    if submitted and query.strip():
        with st.spinner("Running pipeline…"):
            try:
                resp = requests.post(API_URL, json={"query": query}, timeout=120)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.ConnectionError:
                st.error("⚠️  Cannot reach the API. Start uvicorn on port 8000 first.")
                st.stop()
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()

        # ── Result header ──
        col_verdict, col_route = st.columns([3, 2])
        with col_verdict:
            st.markdown(verdict_stamp(data["grounded"]), unsafe_allow_html=True)
        with col_route:
            st.markdown(
                f"<div style='text-align:right;padding-top:4px'>{route_badge(data['route'])}</div>",
                unsafe_allow_html=True,
            )

        if not data["grounded"] and data.get("failure_reason"):
            st.markdown(f"""
            <div style="background:var(--flagged-bg);border:1px solid #E8C8C3;
                        border-radius:5px;padding:0.6rem 1rem;margin-top:0.5rem;
                        font-family:'JetBrains Mono',monospace;font-size:0.8rem;
                        color:var(--flagged)">
            ⚑ {data['failure_reason']}
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        # ── Two-column: answer | sources ──
        col_ans, col_src = st.columns([3, 2])

        with col_ans:
            st.markdown("""
            <div style="font-family:'Lora',serif;font-size:0.78rem;color:#9A9690;
                        text-transform:uppercase;letter-spacing:0.07em;
                        margin-bottom:0.4rem">Answer</div>""",
            unsafe_allow_html=True)
            answer_html = data["answer"].replace("\n", "<br>")
            st.markdown(f'<div class="answer-block">{answer_html}</div>',
                        unsafe_allow_html=True)

        with col_src:
            st.markdown("""
            <div style="font-family:'Lora',serif;font-size:0.78rem;color:#9A9690;
                        text-transform:uppercase;letter-spacing:0.07em;
                        margin-bottom:0.4rem">Sources</div>""",
            unsafe_allow_html=True)
            sources = data.get("sources", [])
            if sources:
                for i, src in enumerate(sources, 1):
                    render_source_card(i, src)
            else:
                st.caption("No sources returned.")

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        # ── Side-by-side answer vs evidence ──
        context_passages = data.get("context", [])
        if sources or context_passages:
            with st.expander("🔍  Answer vs. Evidence — side-by-side"):
                st.markdown("""
                <p style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                           color:#9A9690;margin-bottom:0.8rem">
                Compare the generated answer against the raw retrieved passages it
                was grounded on. Spot any divergence directly.
                </p>""", unsafe_allow_html=True)
                ev_left, ev_right = st.columns(2)
                with ev_left:
                    st.markdown("**Generated answer**")
                    st.markdown(f'<div class="answer-block" style="min-height:120px">'
                                f'{answer_html}</div>', unsafe_allow_html=True)
                with ev_right:
                    st.markdown("**Retrieved evidence passages**")
                    for i, src in enumerate(sources, 1):
                        label = src.get("file") or src.get("title") or src.get("url", "")
                        passage = context_passages[i-1] if i-1 < len(context_passages) else ""
                        passage_html = passage.replace("\n", "<br>") if passage else \
                            "<em style='color:#9A9690'>No passage text available.</em>"
                        st.markdown(f"""
                        <div class="source-card" style="margin-bottom:0.5rem">
                            <div class="src-num">Passage [{i}] — {label}</div>
                            <div style="font-family:'JetBrains Mono',monospace;
                                        font-size:0.78rem;color:#4A4843;
                                        line-height:1.6;margin-top:4px">
                                {passage_html}
                            </div>
                        </div>""", unsafe_allow_html=True)

        # ── Show your work trace ──
        with st.expander("🧾  Show your work — execution trace"):
            render_trace(data)


# ══════════════════════════════════════════════════════════════════════════════
# Page: Dashboard
# ══════════════════════════════════════════════════════════════════════════════

elif "Dashboard" in nav:
    st.markdown("""
    <h1 style="font-family:'Lora',serif;font-size:2rem;font-weight:700;
               margin-bottom:0.2rem">Observatory</h1>
    <p style="color:#9A9690;font-size:0.9rem;margin-bottom:1.8rem">
    Aggregate verification statistics across all queries in this session.
    </p>""", unsafe_allow_html=True)

    try:
        from app.db import (get_analytics_summary, get_grounding_trend,
                            get_cost_per_verified_answer)
        summary  = get_analytics_summary()
        trend    = get_grounding_trend(30)
        cpv      = get_cost_per_verified_answer()
        rag_n    = summary["route_counts"]["rag"]
        web_n    = summary["route_counts"]["web_search"]

    except Exception as e:
        st.error(f"Cannot connect to Postgres: {e}")
        st.stop()

    # ── Hero metrics ──
    m1, m2, m3, m4, m5 = st.columns(5)
    metrics = [
        (f"{summary['total_queries']}", "Total queries"),
        (f"{summary['grounding_success_rate_pct']:.1f}%", "Grounding rate"),
        (f"{summary['avg_latency_ms']:.0f} ms", "Avg latency"),
        (f"${cpv:.6f}", "Cost / verified ans."),
        (f"${summary['total_estimated_cost_usd']:.5f}", "Total est. cost"),
    ]
    for col, (val, label) in zip([m1, m2, m3, m4, m5], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Charts row ──
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("""
        <div style="background:#fff;border:1px solid #DDD9D0;border-radius:8px;
                    padding:1.2rem 1.4rem">
        <div style="font-family:'Lora',serif;font-size:0.9rem;font-weight:600;
                    margin-bottom:0.2rem">Routing split</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                    color:#9A9690;margin-bottom:1rem">
            RAG vs. web-search over all queries
        </div>""", unsafe_allow_html=True)
        st.markdown(routing_split_svg(rag_n, web_n), unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;gap:1.5rem;margin-top:0.8rem;
                    font-family:'JetBrains Mono',monospace;font-size:0.78rem">
          <span style="color:#3D7A5A">📚 RAG: {rag_n}</span>
          <span style="color:#5B4FCF">🌐 Web: {web_n}</span>
        </div>
        </div>""", unsafe_allow_html=True)

    with ch2:
        st.markdown("""
        <div style="background:#fff;border:1px solid #DDD9D0;border-radius:8px;
                    padding:1.2rem 1.4rem">
        <div style="font-family:'Lora',serif;font-size:0.9rem;font-weight:600;
                    margin-bottom:0.2rem">Grounding trend</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                    color:#9A9690;margin-bottom:1rem">
            Rolling 5-query grounding rate, last 30 queries
        </div>""", unsafe_allow_html=True)
        st.markdown(grounding_sparkline_svg(trend), unsafe_allow_html=True)
        grounding_n = int(summary["total_queries"] *
                          summary["grounding_success_rate_pct"] / 100)
        st.markdown(f"""
        <div style="display:flex;gap:1.5rem;margin-top:0.8rem;
                    font-family:'JetBrains Mono',monospace;font-size:0.78rem">
          <span style="color:#3D7A5A">✦ Verified: {grounding_n}</span>
          <span style="color:#A04030">⚑ Flagged: {summary['total_queries'] - grounding_n}</span>
        </div>
        </div>""", unsafe_allow_html=True)

    # ── Cost breakdown ──
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#fff;border:1px solid #DDD9D0;border-radius:8px;
                padding:1.2rem 1.4rem">
    <div style="font-family:'Lora',serif;font-size:0.9rem;font-weight:600;
                margin-bottom:0.7rem">Cost accounting</div>
    """, unsafe_allow_html=True)

    ca, cb, cc = st.columns(3)
    cost_items = [
        ("Avg cost / query",          f"${summary['avg_estimated_cost_usd']:.6f}"),
        ("Cost / verified answer",    f"${cpv:.6f}"),
        ("Total est. spend",          f"${summary['total_estimated_cost_usd']:.5f}"),
    ]
    for col, (label, val) in zip([ca, cb, cc], cost_items):
        with col:
            st.markdown(f"""
            <div style="text-align:center">
                <div style="font-family:'JetBrains Mono',monospace;font-size:1.15rem;
                            font-weight:500;color:#1C1B18">{val}</div>
                <div style="font-family:'Inter',sans-serif;font-size:0.75rem;
                            color:#9A9690;margin-top:3px">{label}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Page: Ledger
# ══════════════════════════════════════════════════════════════════════════════

elif "Ledger" in nav:
    st.markdown("""
    <h1 style="font-family:'Lora',serif;font-size:2rem;font-weight:700;
               margin-bottom:0.2rem">Verification Ledger</h1>
    <p style="color:#9A9690;font-size:0.9rem;margin-bottom:1.8rem">
    Complete record of every query — grounding verdict, route, latency, cost.
    Click any row to expand the full answer and sources.
    </p>""", unsafe_allow_html=True)

    try:
        from app.db import get_recent_logs, get_analytics_summary
        logs    = get_recent_logs(50)
        summary = get_analytics_summary()
    except Exception as e:
        st.error(f"Cannot connect to Postgres: {e}")
        st.stop()

    if not logs:
        st.info("No queries logged yet. Run a query from the Query tab first.")
        st.stop()

    # ── Hero stat ──
    grate = summary["grounding_success_rate_pct"]
    bar_w = int(grate * 2.2)
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #DDD9D0;border-radius:8px;
                padding:1.2rem 1.4rem;margin-bottom:1.4rem">
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                    color:#9A9690;text-transform:uppercase;letter-spacing:0.06em;
                    margin-bottom:0.5rem">Grounding pass-rate — all time</div>
        <div style="display:flex;align-items:center;gap:1rem">
            <div style="font-family:'Lora',serif;font-size:2.2rem;font-weight:700;
                        color:{'#3D7A5A' if grate >= 50 else '#A04030'}">{grate:.1f}%</div>
            <div style="flex:1">
                <div style="background:#EDEAE2;border-radius:4px;height:10px;overflow:hidden">
                    <div style="background:{'#3D7A5A' if grate >= 50 else '#A04030'};
                                height:10px;width:{grate:.0f}%;
                                border-radius:4px;transition:width 0.4s"></div>
                </div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                            color:#9A9690;margin-top:4px">
                    {summary['total_queries']} queries total
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Column headers ──
    st.markdown("""
    <div style="display:grid;grid-template-columns:80px 1fr 90px 80px 90px;
                gap:0.5rem;padding:0.4rem 0.8rem;
                font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                color:#9A9690;text-transform:uppercase;letter-spacing:0.05em;
                border-bottom:1px solid #DDD9D0;margin-bottom:0.5rem">
      <span>Verdict</span><span>Query</span>
      <span>Route</span><span>Latency</span><span>Time</span>
    </div>""", unsafe_allow_html=True)

    # ── Rows ──
    for row in logs:
        verdict_icon = "✦" if row["grounded"] else "⚑"
        verdict_col  = "#3D7A5A" if row["grounded"] else "#A04030"
        route_icon   = "📚" if row["route"] == "rag" else "🌐"
        ts = str(row["created_at"])[:16].replace("T", " ")
        short_q = (row["query"][:72] + "…") if len(row["query"]) > 72 else row["query"]

        with st.expander(
            f"{verdict_icon}  {short_q}",
            expanded=False,
        ):
            ec1, ec2, ec3 = st.columns([2, 2, 1])
            with ec1:
                st.markdown(verdict_stamp(row["grounded"]), unsafe_allow_html=True)
                st.markdown(f"""
                <div style="margin-top:0.8rem;font-family:'JetBrains Mono',monospace;
                            font-size:0.75rem;color:#9A9690">
                {route_icon} {row['route']} &nbsp;·&nbsp;
                {row['latency_ms']} ms &nbsp;·&nbsp;
                ${float(row['estimated_cost_usd']):.6f} &nbsp;·&nbsp;
                {ts}
                </div>""", unsafe_allow_html=True)

                if row.get("failure_reason"):
                    st.markdown(f"""
                    <div style="background:var(--flagged-bg);border:1px solid #E8C8C3;
                                border-radius:4px;padding:0.5rem 0.8rem;margin-top:0.6rem;
                                font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                color:#A04030">
                    ⚑ {row['failure_reason']}</div>""", unsafe_allow_html=True)

            with ec2:
                st.markdown("**Answer**")
                ans_html = str(row.get("answer", "")).replace("\n", "<br>")
                st.markdown(f'<div class="answer-block" style="font-size:0.85rem;'
                            f'max-height:180px;overflow-y:auto">{ans_html}</div>',
                            unsafe_allow_html=True)

            with ec3:
                st.markdown("**Sources**")
                try:
                    srcs = row["sources"] if isinstance(row["sources"], list) \
                           else json.loads(row["sources"] or "[]")
                    for i, s in enumerate(srcs, 1):
                        render_source_card(i, s)
                except Exception:
                    st.caption("—")
