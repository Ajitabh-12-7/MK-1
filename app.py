"""
MARS — app.py
Streamlit UI — Multi-Agent Research System

Design: Dark glassmorphic, Buttermax-inspired (Design Doc)
Fonts: Clash Display (headings) · Inter (body) · JetBrains Mono (code)
"""

import streamlit as st
import time
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="MARS — Multi-Agent Research System",
    page_icon="🔭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

import config
from orchestrator import run_pipeline

logging.basicConfig(level=logging.INFO)

# ── CSS Design System ─────────────────────────────────────────────────────────

def _inject_css():
    st.markdown(
        """
        <style>
        /* ── Google Fonts ─────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        @import url('https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&display=swap');

        /* ── Design Tokens ────────────────────────────────────────── */
        :root {
            --color-bg:           #0F172A;
            --color-surface:      #1E293B;
            --color-surface-hover:#334155;
            --color-primary:      #7C3AED;
            --color-primary-light:#A78BFA;
            --color-accent:       #6366F1;
            --color-text:         #F8FAFC;
            --color-text-muted:   #94A3B8;
            --color-success:      #10B981;
            --color-warning:      #F59E0B;
            --color-error:        #EF4444;
            --radius-card:        16px;
            --radius-btn:         12px;
            --blur-glass:         12px;
            --transition-default: 200ms ease-out;
        }

        /* ── Global reset + background ────────────────────────────── */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--color-bg) !important;
            color: var(--color-text) !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Background gradient mesh */
        [data-testid="stAppViewContainer"]::before {
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.13) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.13) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }

        /* Hide Streamlit chrome */
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stDecoration"] { display: none; }
        [data-testid="stToolbar"] { display: none; }
        .stDeployButton { display: none; }

        /* ── Typography ───────────────────────────────────────────── */
        h1, h2, h3 {
            font-family: 'Clash Display', 'Inter', sans-serif !important;
            color: var(--color-text) !important;
        }

        /* ── Hero ─────────────────────────────────────────────────── */
        .mars-hero {
            text-align: center;
            padding: 3rem 0 1.5rem;
            animation: heroFadeIn 0.6s ease-out both;
        }
        .mars-hero .badge {
            display: inline-block;
            background: rgba(124,58,237,0.15);
            border: 1px solid rgba(124,58,237,0.3);
            color: var(--color-primary-light);
            border-radius: 999px;
            padding: 4px 14px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }
        .mars-hero h1 {
            font-size: clamp(2.2rem, 5vw, 3.5rem);
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #F8FAFC 20%, var(--color-primary-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 0.75rem;
            line-height: 1.1;
        }
        .mars-hero p {
            color: var(--color-text-muted);
            font-size: 1.05rem;
            font-weight: 400;
            max-width: 520px;
            margin: 0 auto 0.5rem;
            line-height: 1.6;
        }

        @keyframes heroFadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ── Input area ───────────────────────────────────────────── */
        [data-testid="stTextInput"] > div > div > input {
            background: rgba(15, 23, 42, 0.85) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 12px !important;
            color: var(--color-text) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 15px !important;
            padding: 14px 18px !important;
            transition: border-color var(--transition-default), box-shadow var(--transition-default) !important;
        }
        [data-testid="stTextInput"] > div > div > input:focus {
            border-color: var(--color-primary) !important;
            box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
            outline: none !important;
        }
        [data-testid="stTextInput"] label {
            color: var(--color-text-muted) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        /* ── Primary button ───────────────────────────────────────── */
        [data-testid="stButton"] > button {
            background: linear-gradient(135deg, #7C3AED 0%, #6366F1 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius-btn) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            padding: 12px 32px !important;
            width: 100% !important;
            cursor: pointer !important;
            transition: transform 150ms ease-out, box-shadow 150ms ease-out !important;
        }
        [data-testid="stButton"] > button:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 0 24px rgba(124,58,237,0.4) !important;
        }
        [data-testid="stButton"] > button:active {
            transform: scale(0.98) !important;
        }

        /* ── Agent pipeline cards ─────────────────────────────────── */
        .agent-cards-row {
            display: flex;
            gap: 14px;
            margin: 2rem 0 1rem;
        }
        /* Streamlit column gap fix */
        [data-testid="column"] { padding: 0 6px !important; }
        .agent-card {
            flex: 1;
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(var(--blur-glass));
            -webkit-backdrop-filter: blur(var(--blur-glass));
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: var(--radius-card);
            padding: 18px 16px;
            transition: border-color var(--transition-default), transform 200ms ease-out;
            position: relative;
            overflow: hidden;
        }
        .agent-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255,255,255,0.13);
        }
        .agent-card.idle   { border-color: rgba(255,255,255,0.07); }
        .agent-card.running {
            border-color: var(--color-primary);
            box-shadow: 0 0 0 1px rgba(124,58,237,0.3), 0 0 20px rgba(124,58,237,0.15);
            animation: borderPulse 1.4s ease-in-out infinite;
        }
        .agent-card.complete {
            border-color: var(--color-success);
            box-shadow: 0 0 12px rgba(16,185,129,0.15);
        }
        .agent-card.error {
            border-color: var(--color-error);
        }

        @keyframes borderPulse {
            0%, 100% { box-shadow: 0 0 0 1px rgba(124,58,237,0.3), 0 0 20px rgba(124,58,237,0.1); }
            50%       { box-shadow: 0 0 0 2px rgba(124,58,237,0.5), 0 0 30px rgba(124,58,237,0.25); }
        }

        .agent-card .card-icon {
            font-size: 28px;
            margin-bottom: 10px;
            display: block;
        }
        .agent-card .card-name {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 14px;
            color: var(--color-text);
            margin-bottom: 6px;
        }
        .agent-card .card-desc {
            font-size: 12px;
            color: var(--color-text-muted);
            line-height: 1.4;
            margin-bottom: 12px;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.03em;
        }
        .badge-idle     { background: rgba(148,163,184,0.1); color: var(--color-text-muted); }
        .badge-running  { background: rgba(245,158,11,0.15); color: var(--color-warning); }
        .badge-complete { background: rgba(16,185,129,0.15); color: var(--color-success); }
        .badge-error    { background: rgba(239,68,68,0.15);  color: var(--color-error); }

        /* ── Progress timeline ────────────────────────────────────── */
        .progress-timeline {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            margin: 1.5rem 0;
        }
        .timeline-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .timeline-dot {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            border: 2px solid rgba(255,255,255,0.1);
            background: rgba(30,41,59,0.6);
            transition: all 300ms ease-out;
        }
        .timeline-dot.active  { border-color: var(--color-primary); background: rgba(124,58,237,0.2); }
        .timeline-dot.done    { border-color: var(--color-success); background: rgba(16,185,129,0.2); }
        .timeline-label {
            font-size: 11px;
            color: var(--color-text-muted);
            font-weight: 500;
            white-space: nowrap;
        }
        .timeline-label.done  { color: var(--color-success); }
        .timeline-label.active { color: var(--color-primary-light); }
        .timeline-line {
            width: 60px;
            height: 2px;
            background: rgba(255,255,255,0.08);
            margin: 0 4px;
            margin-bottom: 22px;
            transition: background 500ms ease-out;
        }
        .timeline-line.done { background: var(--color-primary); }

        /* ── Report panel ─────────────────────────────────────────── */
        .report-panel {
            background: rgba(30,41,59,0.6);
            backdrop-filter: blur(var(--blur-glass));
            -webkit-backdrop-filter: blur(var(--blur-glass));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: var(--radius-card);
            padding: 28px 28px 20px;
            margin-top: 2rem;
            animation: reportReveal 0.4s cubic-bezier(0.16,1,0.3,1) both;
        }
        .report-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .report-panel-title {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 15px;
            color: var(--color-text);
        }
        @keyframes reportReveal {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ── Markdown report typography ───────────────────────────── */
        .report-panel h1 { font-size: 1.7rem; margin-bottom: 0.5rem; }
        .report-panel h2 { font-size: 1.2rem; color: var(--color-primary-light); margin-top: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px; }
        .report-panel h3 { font-size: 1.05rem; color: var(--color-text); }
        .report-panel p  { color: rgba(248,250,252,0.85); line-height: 1.75; margin: 0.75rem 0; }
        .report-panel a  { color: var(--color-primary-light); text-decoration: none; }
        .report-panel a:hover { text-decoration: underline; }
        .report-panel ol, .report-panel ul { padding-left: 1.5rem; color: rgba(248,250,252,0.85); }
        .report-panel li { margin: 0.4rem 0; line-height: 1.6; }
        .report-panel code { font-family: 'JetBrains Mono', monospace; font-size: 12.5px; background: rgba(15,23,42,0.7); padding: 2px 6px; border-radius: 4px; color: var(--color-primary-light); }

        /* ── Source chips ─────────────────────────────────────────── */
        .source-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1.5rem; }
        .source-chip {
            background: rgba(124,58,237,0.1);
            border: 1px solid rgba(124,58,237,0.25);
            border-radius: 999px;
            padding: 4px 12px;
            font-size: 11px;
            color: var(--color-primary-light);
            text-decoration: none;
            transition: background var(--transition-default);
            white-space: nowrap;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
        }
        .source-chip:hover { background: rgba(124,58,237,0.2); color: white; }

        /* ── Expanders ────────────────────────────────────────────── */
        [data-testid="stExpander"] {
            background: rgba(15,23,42,0.5) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] summary {
            color: var(--color-text-muted) !important;
            font-size: 13px !important;
        }

        /* ── Alerts / Warning strip ───────────────────────────────── */
        .warning-strip {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 10px;
            padding: 12px 16px;
            color: var(--color-error);
            font-size: 13px;
            margin: 1rem 0;
        }

        /* ── Stats bar ────────────────────────────────────────────── */
        .stats-bar {
            display: flex;
            gap: 24px;
            padding: 14px 0;
            border-top: 1px solid rgba(255,255,255,0.07);
            margin-top: 1rem;
        }
        .stat-item { display: flex; flex-direction: column; gap: 2px; }
        .stat-label { font-size: 11px; color: var(--color-text-muted); font-weight: 500; }
        .stat-value { font-size: 18px; font-weight: 700; color: var(--color-text); font-family: 'Clash Display', sans-serif; }

        /* ── Mobile responsive ────────────────────────────────────── */
        @media (max-width: 768px) {
            .agent-cards-row { flex-direction: column; }
            .mars-hero h1 { font-size: 2rem; }
            .mars-hero p  { font-size: 0.95rem; }
            .timeline-line { width: 30px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Helper: single agent card HTML ──────────────────────────────────────────

def _card_html(icon: str, name: str, desc: str, state: str, detail: str = "") -> str:
    badge_map = {
        "idle":     ("●", "Idle",     "idle"),
        "running":  ("◌", "Running…", "running"),
        "complete": ("✓", "Done",     "complete"),
        "error":    ("✗", "Error",    "error"),
    }
    dot, label, cls = badge_map.get(state, badge_map["idle"])
    detail_html = (
        f'<div style="margin-top:8px;font-size:11px;color:var(--color-text-muted);'
        f'font-family:\'JetBrains Mono\',monospace;line-height:1.5;word-break:break-all;">'
        f'{detail}</div>'
    ) if detail else ""
    return (
        f'<div class="agent-card {cls}">'
        f'<span class="card-icon">{icon}</span>'
        f'<div class="card-name">{name}</div>'
        f'<div class="card-desc">{desc}</div>'
        f'<span class="status-badge badge-{cls}">{dot} {label}</span>'
        f'{detail_html}</div>'
    )


def _timeline_html(step: int) -> str:
    """step: 0=none, 1=search done, 2=extract done, 3=write done"""
    def dot_cls(n): return "done" if step >= n else ("active" if step == n - 1 else "")
    def line_cls(n): return "done" if step >= n else ""
    def lbl_cls(n): return "done" if step >= n else ("active" if step == n - 1 else "")
    return (
        '<div class="progress-timeline">'
        f'<div class="timeline-step"><div class="timeline-dot {dot_cls(1)}">🔍</div><div class="timeline-label {lbl_cls(1)}">Search</div></div>'
        f'<div class="timeline-line {line_cls(1)}"></div>'
        f'<div class="timeline-step"><div class="timeline-dot {dot_cls(2)}">📄</div><div class="timeline-label {lbl_cls(2)}">Extract</div></div>'
        f'<div class="timeline-line {line_cls(2)}"></div>'
        f'<div class="timeline-step"><div class="timeline-dot {dot_cls(3)}">✍️</div><div class="timeline-label {lbl_cls(3)}">Write</div></div>'
        '</div>'
    )


def _source_chips_html(urls: list[str]) -> str:
    chips = "".join(
        f'<a href="{u}" target="_blank" class="source-chip" title="{u}">{u[:45]}{"…" if len(u) > 45 else ""}</a>'
        for u in urls
    )
    return f'<div class="source-chips">{chips}</div>'


# ── Main app ──────────────────────────────────────────────────────────────────

def main():
    _inject_css()

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="mars-hero">'
        '<div class="badge">🔭 MARS · Multi-Agent Research System</div>'
        '<h1>Deep Research, Automated.</h1>'
        '<p>Enter any topic. Three specialised AI agents search the web, '
        'extract facts, and synthesise a publication-ready report — automatically.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── API key check ──────────────────────────────────────────────────────────
    missing = config.validate_keys()
    if missing:
        st.markdown(
            f'<div class="warning-strip">⚠️ Missing API keys: <strong>{", ".join(missing)}</strong>. '
            f'Add them to your <code>.env</code> file and restart the app.</div>',
            unsafe_allow_html=True,
        )

    # ── Input ──────────────────────────────────────────────────────────────────
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. LangGraph multi-agent AI systems 2025",
        label_visibility="collapsed",
    )
    run_clicked = st.button("🚀  Run Research", disabled=bool(missing))

    # ── Agent cards — using st.columns (no HTML overflow) ──────────────────────
    cards_area = st.empty()
    timeline_area = st.empty()

    def _render_cards(s1="idle", s2="idle", s3="idle", d1="", d2="", d3="", step=0):
        with cards_area.container():
            c1, c2, c3 = st.columns(3)
            c1.markdown(_card_html("🔍", "Web Searcher",   "Queries the web via Tavily, returns top sources.", s1, d1), unsafe_allow_html=True)
            c2.markdown(_card_html("📄", "Fact Extractor",  "Fetches pages, parses HTML, extracts facts with Groq.", s2, d2), unsafe_allow_html=True)
            c3.markdown(_card_html("✍️", "Report Writer",   "Synthesises grounded, citation-backed report.", s3, d3), unsafe_allow_html=True)
        timeline_area.markdown(_timeline_html(step), unsafe_allow_html=True)

    _render_cards()

    # ── Run pipeline ────────────────────────────────────────────────────────────
    if run_clicked:
        if not topic.strip():
            st.warning("Please enter a research topic.")
        else:
            result_placeholder = st.empty()
            start_time = time.time()

            # Phase 1: Searching
            _render_cards(s1="running", step=0)
            with st.status("🔍 Agent 1 — Searching the web…", expanded=False) as search_status:
                from agents.searcher import search_node
                search_state = search_node({"topic": topic})
                search_results = search_state.get("search_results", [])
                search_err = search_state.get("error")
                if search_err and not search_results:
                    search_status.update(label=f"❌ Search failed: {search_err}", state="error")
                    _render_cards(s1="error", d1=search_err, step=0)
                    st.error(f"Search agent failed: {search_err}")
                    st.stop()
                else:
                    search_status.update(label=f"✅ Found {len(search_results)} results", state="complete")

            _render_cards(
                s1="complete",
                s2="running",
                d1=f"{len(search_results)} sources found",
                step=1,
            )

            time.sleep(config.AGENT_SLEEP_SECONDS)  # Groq rate limit guard

            # Show intermediate search results
            with st.expander(f"🔍 Search Results ({len(search_results)} sources)", expanded=False):
                for r in search_results:
                    st.markdown(
                        f"**[{r.get('title','No title')}]({r.get('url','#')})**\n\n"
                        f"{r.get('snippet','')[:200]}…",
                        unsafe_allow_html=False,
                    )
                    st.divider()

            # Phase 2: Extracting
            with st.status("📄 Agent 2 — Extracting facts from pages…", expanded=False) as extract_status:
                from agents.extractor import extract_node
                extract_state = extract_node({**search_state})
                extracted_facts = extract_state.get("extracted_facts", {})
                extract_err = extract_state.get("error")
                fact_count = sum(len(f) for f in extracted_facts.values())
                if extract_err and not extracted_facts:
                    extract_status.update(label=f"❌ Extraction failed: {extract_err}", state="error")
                    _render_cards(s1="complete", s2="error", d1=f"{len(search_results)} sources", d2=extract_err, step=1)
                    st.warning(f"No facts extracted. {extract_err}")
                else:
                    extract_status.update(
                        label=f"✅ Extracted {fact_count} facts from {len(extracted_facts)} sources",
                        state="complete",
                    )

            _render_cards(
                s1="complete",
                s2="complete",
                s3="running",
                d1=f"{len(search_results)} sources",
                d2=f"{fact_count} facts from {len(extracted_facts)} pages",
                step=2,
            )

            time.sleep(config.AGENT_SLEEP_SECONDS)

            # Show intermediate extraction results
            with st.expander(f"📄 Extracted Facts ({fact_count} total)", expanded=False):
                for url, facts in extracted_facts.items():
                    st.markdown(f"**{url[:60]}…**" if len(url) > 60 else f"**{url}**")
                    for f in facts:
                        st.markdown(f"- {f}")
                    st.divider()

            # Phase 3: Writing
            with st.status("✍️ Agent 3 — Writing research report…", expanded=False) as write_status:
                from agents.writer import write_node
                write_state = write_node({**extract_state, "topic": topic})
                report = write_state.get("report", "")
                write_err = write_state.get("error")
                if write_err and not report:
                    write_status.update(label=f"❌ Writing failed: {write_err}", state="error")
                else:
                    write_status.update(
                        label=f"✅ Report ready ({len(report):,} chars)",
                        state="complete",
                    )

            elapsed = round(time.time() - start_time, 1)
            _render_cards(
                s1="complete",
                s2="complete",
                s3="complete",
                d1=f"{len(search_results)} sources",
                d2=f"{fact_count} facts from {len(extracted_facts)} pages",
                d3=f"{len(report):,} chars · {elapsed}s",
                step=3,
            )

            # ── Stats bar ────────────────────────────────────────────────────────
            st.markdown(
                f"""
                <div class="stats-bar">
                    <div class="stat-item">
                        <div class="stat-label">SOURCES SEARCHED</div>
                        <div class="stat-value">{len(search_results)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">FACTS EXTRACTED</div>
                        <div class="stat-value">{fact_count}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">SOURCES CITED</div>
                        <div class="stat-value">{len(extracted_facts)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">PIPELINE TIME</div>
                        <div class="stat-value">{elapsed}s</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ── Report output panel ────────────────────────────────────────────
            if report:
                st.markdown(
                    '<div class="report-panel">'
                    '<div class="report-panel-header">'
                    '<span class="report-panel-title">📋 Research Report</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(report)

                # Source chips
                if extracted_facts:
                    st.markdown(
                        "**Sources:**" + _source_chips_html(list(extracted_facts.keys())),
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

                # Raw markdown copy block
                with st.expander("📋 Copy Raw Markdown", expanded=False):
                    st.code(report, language="markdown")

            elif write_err:
                st.error(f"Report generation error: {write_err}")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="text-align:center;margin-top:3rem;padding:1rem 0;border-top:1px solid rgba(255,255,255,0.06);">'
        '<p style="color:var(--color-text-muted);font-size:12px;margin:0;">'
        '🔭 MARS · LangGraph · Groq · Tavily · Streamlit'
        '</p></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
