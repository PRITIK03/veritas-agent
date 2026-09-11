"""Veritas Agent — internal engineering console.

A restrained, intent-led Streamlit UI: one accent colour, a clear type
hierarchy, and no default-Streamlit chrome. Two workspaces:
  - Ask:        run a query and inspect the answer, grounding verdict, sources,
                and run statistics.
  - Analytics:  a small dashboard over the /analytics endpoint.

Set VERITAS_API_KEY (same value the API expects in the X-API-Key header).
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("VERITAS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("VERITAS_API_KEY", "")
REQUEST_TIMEOUT = 180

ACCENT = "#0F766E"
INK = "#0F172A"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#15803D"
WARNING = "#B45309"
DANGER = "#B91C1C"

st.set_page_config(page_title="Veritas Agent", layout="wide")

st.markdown(
    f"""
    <style>
        .stApp {{
            background: #FAFAF9;
            color: {INK};
        }}
        #MainMenu, footer, header {{ visibility: hidden; }}

        html, body, [class*="css"] {{
            font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
        }}

        /* Kill default Streamlit accent colour on interactive widgets. */
        .stButton > button {{
            background: {ACCENT};
            color: #FFFFFF;
            border: 1px solid {ACCENT};
            border-radius: 4px;
            font-weight: 600;
            letter-spacing: 0.01em;
            padding: 0.45rem 1.1rem;
        }}
        .stButton > button:hover {{
            background: #0B5F58;
            border-color: #0B5F58;
        }}
        .stTextArea textarea, .stTextInput input {{
            border-radius: 4px;
            border: 1px solid {BORDER};
        }}
        .stTextArea textarea:focus, .stTextInput input:focus {{
            border-color: {ACCENT};
            box-shadow: 0 0 0 1px {ACCENT};
        }}

        .va-title {{
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.01em;
            margin-bottom: 2px;
        }}
        .va-sub {{
            color: {MUTED};
            font-size: 13px;
            margin-bottom: 22px;
        }}
        .va-section {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: {MUTED};
            border-bottom: 1px solid {BORDER};
            padding-bottom: 6px;
            margin: 26px 0 14px 0;
        }}
        .va-answer {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-left: 3px solid {ACCENT};
            border-radius: 4px;
            padding: 18px 20px;
            font-size: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
        }}

        .va-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .va-badge-grounded {{ background: #DCFCE7; color: {SUCCESS}; border: 1px solid #BBF7D0; }}
        .va-badge-unverified {{ background: #FEF3C7; color: {WARNING}; border: 1px solid #FDE68A; }}

        .va-metric {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 12px 14px;
        }}
        .va-metric-label {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {MUTED};
            font-weight: 700;
        }}
        .va-metric-value {{
            font-size: 20px;
            font-weight: 700;
            margin-top: 2px;
        }}

        .va-source {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .va-source-idx {{
            color: {ACCENT};
            font-weight: 700;
            margin-right: 8px;
        }}

        .va-bar-track {{
            background: {BORDER};
            border-radius: 999px;
            height: 10px;
            width: 100%;
            overflow: hidden;
        }}
        .va-bar-fill {{
            height: 100%;
            border-radius: 999px;
            background: {ACCENT};
        }}
        .va-bar-success {{ background: {SUCCESS}; }}

        .va-st-panel {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 18px 20px;
        }}
        .va-st-row {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #F1F5F9;
            padding: 9px 0;
            font-size: 13px;
        }}
        .va-st-row:last-child {{ border-bottom: none; }}
        .va-st-key {{ color: {MUTED}; }}
        .va-st-val {{ font-weight: 600; }}

        .va-tabs button[role="tab"] {{
            font-weight: 600;
            color: {MUTED};
        }}
        .va-tabs button[role="tab"][aria-selected="true"] {{
            color: {ACCENT};
            border-bottom-color: {ACCENT};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _headers():
    return {"X-API-Key": API_KEY} if API_KEY else {}


def _metric(label, value):
    return (
        f'<div class="va-metric"><div class="va-metric-label">{label}</div>'
        f'<div class="va-metric-value">{value}</div></div>'
    )


def _badge(grounded: bool) -> str:
    if grounded:
        return '<span class="va-badge va-badge-grounded">GROUNDED</span>'
    return '<span class="va-badge va-badge-unverified">UNVERIFIED</span>'


st.markdown('<div class="va-title">Veritas Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="va-sub">Grounded question answering over internal policy documents and the live web.</div>',
    unsafe_allow_html=True,
)

tab_ask, tab_analytics = st.tabs(["Ask", "Analytics"])

with tab_ask:
    query = st.text_area(
        "Query",
        height=90,
        placeholder="e.g. Can a fully remote employee expense a standing desk, and what is the 2025 mileage rate?",
        label_visibility="collapsed",
    )

    run = st.button("Run query")

    if run and query.strip():
        with st.spinner("Retrieving and verifying..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/query",
                    json={"query": query},
                    headers=_headers(),
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.ConnectionError:
                st.error("Could not reach the API. Is uvicorn running on port 8000?")
                st.stop()
            except requests.exceptions.HTTPError as e:
                st.error(f"API error {resp.status_code}: {resp.text or e}")
                st.stop()
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()

        col_answer, col_verdict = st.columns([5, 1])
        with col_answer:
            st.markdown('<div class="va-section">Answer</div>', unsafe_allow_html=True)
        with col_verdict:
            st.markdown(
                f'<div class="va-section" style="text-align:right;">Verdict</div>',
                unsafe_allow_html=True,
            )

        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'<div class="va-answer">{data["answer"]}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(_badge(data["grounded"]), unsafe_allow_html=True)

        if not data["grounded"] and data.get("failure_reason"):
            st.markdown(
                f'<div style="color:{WARNING};font-size:13px;margin-top:10px;">'
                f'Grounding note: {data["failure_reason"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="va-section">Run statistics</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(_metric("Route", data["route"]), unsafe_allow_html=True)
        m2.markdown(_metric("Latency", f'{data["latency_ms"]} ms'), unsafe_allow_html=True)
        m3.markdown(
            _metric("Tokens in / out", f'{data["input_tokens"]} / {data["output_tokens"]}'),
            unsafe_allow_html=True,
        )
        m4.markdown(
            _metric("Estimated cost", f'${data["estimated_cost_usd"]:.6f}'),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="va-section">Sources</div>', unsafe_allow_html=True)
        if data["sources"]:
            for i, src in enumerate(data["sources"], start=1):
                if "file" in src:
                    label = f'{src["file"]} · chunk {src.get("chunk_id", "—")}'
                else:
                    label = src.get("title") or src.get("url") or "source"
                st.markdown(
                    f'<div class="va-source"><span class="va-source-idx">[{i}]</span>{label}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div style="color:{MUTED};font-size:13px;">No sources retrieved.</div>',
                unsafe_allow_html=True,
            )

with tab_analytics:
    st.markdown('<div class="va-section">Aggregate metrics</div>', unsafe_allow_html=True)
    try:
        resp = requests.get(f"{API_BASE}/analytics", headers=_headers(), timeout=30)
        resp.raise_for_status()
        a = resp.json()

        total = a["total_queries"]
        rate = a["grounding_success_rate_pct"]
        rag = a["route_counts"]["rag"]
        web = a["route_counts"]["web_search"]
        denom = max(total, 1)

        st.markdown('<div class="va-section">Grounding success</div>', unsafe_allow_html=True)
        bar_class = "va-bar-fill va-bar-success" if rate >= 90 else "va-bar-fill"
        st.markdown(
            f'<div class="va-st-panel">'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;'
            f'font-weight:600;margin-bottom:8px;"><span>{rate:.1f}% grounded</span>'
            f'<span style="color:{MUTED};">{total} queries</span></div>'
            f'<div class="va-bar-track"><div class="{bar_class}" '
            f'style="width:{max(rate, 1.5):.1f}%;"></div></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="va-section">Route split</div>', unsafe_allow_html=True)
        rag_pct = 100.0 * rag / denom
        web_pct = 100.0 * web / denom
        st.markdown(
            f'<div class="va-st-panel">'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;'
            f'margin-bottom:6px;"><span style="color:{MUTED};">RAG</span>'
            f"<span><b>{rag}</b> ({rag_pct:.0f}%)</span></div>"
            f'<div class="va-bar-track" style="margin-bottom:14px;"><div class="va-bar-fill" '
            f'style="width:{max(rag_pct, 1.5):.1f}%;"></div></div>'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;'
            f'margin-bottom:6px;"><span style="color:{MUTED};">Web search</span>'
            f"<span><b>{web}</b> ({web_pct:.0f}%)</span></div>"
            f'<div class="va-bar-track"><div class="va-bar-fill" '
            f'style="width:{max(web_pct, 1.5):.1f}%;background:{MUTED};"></div></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="va-section">Cost and latency</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.markdown(_metric("Avg latency", f'{a["avg_latency_ms"]:.0f} ms'), unsafe_allow_html=True)
        m2.markdown(
            _metric("Avg cost / query", f'${a["avg_estimated_cost_usd"]:.6f}'),
            unsafe_allow_html=True,
        )
        m3.markdown(
            _metric("Total cost", f'${a["total_estimated_cost_usd"]:.6f}'),
            unsafe_allow_html=True,
        )
    except requests.exceptions.ConnectionError:
        st.error("Could not reach the API. Is uvicorn running on port 8000?")
    except requests.exceptions.HTTPError as e:
        st.error(f"API error {resp.status_code}: {resp.text or e}")
    except Exception as e:
        st.error(f"Request failed: {e}")
