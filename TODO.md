# MARS — Multi-Agent Research System
## Master TODO List
> Cross-referenced from: PRD v1.0 · Design Doc · Tech Stack Research
> Author: Ajitabh Mishra (Dan) | Sharda University B.Tech CSE
> Last Updated: March 2026

---

## PHASE 1 — Project Setup & Environment
> Week 1 prereq | Tech Stack doc §10

- [ ] Create project directory structure (`agents/`, `tools/`, `ui/`, `tests/`)
- [ ] Create `requirements.txt` with all pinned dependencies:
  - [ ] `langchain==0.3.x`, `langgraph==0.2.x`
  - [ ] `langchain-groq==0.2.x`, `groq==0.11.x`
  - [ ] `tavily-python==0.5.x`
  - [ ] `httpx==0.27.x`, `beautifulsoup4==4.12.x`, `playwright==1.45.x`
  - [ ] `streamlit==1.35.x`
  - [ ] `langsmith==0.2.x`
  - [ ] `python-dotenv==1.0.x`, `pydantic==2.x`
- [ ] Create `.env` file with placeholders for `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`
- [ ] Create `.gitignore` — exclude `.env`, `__pycache__`, `.venv`
- [ ] Set up `python-dotenv` loading in `config.py`
- [ ] Install and set up LangSmith tracing (`LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_PROJECT`)
- [ ] Set up virtual environment and `pip install -r requirements.txt`
- [ ] Install Playwright browsers: `playwright install chromium`

---

## PHASE 2 — Agent 1: Web Searcher
> PRD §3.1 | Tech Stack §3 (Tavily)

- [ ] Create `agents/searcher.py`
- [ ] Initialise `ChatGroq` LLM with `llama-3.3-70b-versatile`, `temperature=0.7`
- [ ] Integrate `TavilySearchResults` tool from `langchain_community.tools`
- [ ] Configure Tavily to return max 10 results with `title`, `url`, `snippet` fields
- [ ] Implement filtering logic to remove duplicate or irrelevant URLs
- [ ] Define `search_node(state: dict) -> dict` function:
  - [ ] Accept `state["topic"]` as input
  - [ ] Run Tavily search and parse results
  - [ ] Return `state` updated with `state["search_results"]` (list of `{title, url, snippet}`)
- [ ] Add basic error handling (empty results, API timeout)
- [ ] Write CLI test: run `searcher.py` with a sample topic and inspect JSON output

---

## PHASE 3 — Agent 2: Content Extractor
> PRD §3.2 | Tech Stack §4 (httpx + BeautifulSoup4 + Playwright fallback)

- [ ] Create `agents/extractor.py`
- [ ] Implement `fetch_url(url: str) -> str` using `httpx` (async):
  - [ ] Set reasonable timeout (10s)
  - [ ] Return raw HTML on success, `None` on failure (skip, log warning)
- [ ] Implement Playwright fallback for JS-heavy pages:
  - [ ] Detect if `httpx` returns blank/minimal content
  - [ ] Launch headless Chromium, navigate, wait for DOM, return HTML
- [ ] Parse HTML with `BeautifulSoup4` — extract `<p>` and `<article>` tags, strip boilerplate
- [ ] For each URL in `state["search_results"]`, call the fetch + parse pipeline
- [ ] Pass cleaned page text to `ChatGroq` with a fact-extraction prompt:
  - [ ] Prompt: "Extract key facts, statistics, and claims from this text. Attribute each to the source URL."
  - [ ] Parse LLM output into `{url: [fact1, fact2, ...]}`
- [ ] Define `extract_node(state: dict) -> dict`:
  - [ ] Accept `state["search_results"]`
  - [ ] Return `state` updated with `state["extracted_facts"]` (dict of url → facts list)
- [ ] Add `time.sleep(2)` after `search_node` call in orchestrator (Groq rate limit guard)
- [ ] Write CLI test: pass sample URL list, inspect extracted facts output

---

## PHASE 4 — Agent 3: Report Writer
> PRD §3.3 | Tech Stack §2 (Groq LLM)

- [ ] Create `agents/writer.py`
- [ ] Build a structured prompt that includes all extracted facts, grounded with source URLs
- [ ] Instruct LLM to produce a markdown report with these sections:
  - [ ] Executive Summary
  - [ ] Key Findings
  - [ ] Detailed Analysis
  - [ ] Conclusion
  - [ ] References (clickable URLs)
- [ ] Enforce no-hallucination constraint: "Only use facts provided below. Do not add information not in the sources."
- [ ] Define `write_node(state: dict) -> dict`:
  - [ ] Accept `state["extracted_facts"]` and `state["topic"]`
  - [ ] Call `ChatGroq` with the structured prompt
  - [ ] Return `state` updated with `state["report"]` (markdown string)
- [ ] Add `time.sleep(2)` after `extract_node` call in orchestrator
- [ ] Write CLI test: pass sample facts dict, inspect markdown report output

---

## PHASE 5 — Orchestrator (LangGraph Pipeline)
> PRD §3.4 | Tech Stack §1 (LangGraph)

- [ ] Create `orchestrator.py`
- [ ] Define `AgentState` TypedDict with fields:
  - [ ] `topic: str`
  - [ ] `search_results: list`
  - [ ] `extracted_facts: dict`
  - [ ] `report: str`
  - [ ] `error: str | None`
- [ ] Build `StateGraph` with 3 nodes:
  - [ ] Add `search_node` → `extract_node` → `write_node` as sequential edges
  - [ ] Set `search_node` as the entry point
  - [ ] Set `END` after `write_node`
- [ ] Compile the graph: `pipeline = graph.compile()`
- [ ] Implement `run_pipeline(topic: str) -> dict`:
  - [ ] Call `pipeline.invoke({"topic": topic})`
  - [ ] Add `time.sleep(2)` between each agent transition (Groq 30 RPM guard)
  - [ ] Log each agent's start and completion to console
  - [ ] Return final state dict
- [ ] Implement error handling:
  - [ ] Catch agent exceptions, log stack trace, set `state["error"]`
  - [ ] Graceful fallback message if any node fails
  - [ ] Hard cap on retries (max 3) to prevent infinite loops
- [ ] Add exponential backoff on Groq 429 errors (start at 4s)
- [ ] Run full end-to-end CLI test on 3 different topics

---

## PHASE 6 — Streamlit UI
> PRD §3.5 | Design Doc §4, §5, §7

### Setup
- [ ] Create `app.py` (Streamlit entry point)
- [ ] Import Google Fonts (Clash Display, Inter, JetBrains Mono) via CSS injection

### Global CSS & Design System
- [ ] Inject global CSS variables (Design Doc §8 tokens):
  - [ ] `--color-bg: #0F172A`, `--color-surface: #1E293B`, `--color-primary: #7C3AED`
  - [ ] All colour, radius, blur, and transition tokens
- [ ] Apply background gradient mesh: `radial-gradient` ellipses at 20%/80% with violet overlay
- [ ] Set base body font to Inter, heading font to Clash Display

### Layout — Hero Section
- [ ] App logo/name in Clash Display 700 Bold, large
- [ ] Short tagline beneath in Inter muted text
- [ ] Smooth page-load animation: logo fades in + slides from Y+30 over 600ms ease-out

### Layout — Input Section
- [ ] `st.text_input` for topic entry with custom dark styling:
  - [ ] Background `rgba(15,23,42,0.8)`, border `rgba(255,255,255,0.1)`
  - [ ] Focus: border transitions to violet with soft glow ring
  - [ ] Placeholder in muted italic text
- [ ] "Run Research" primary button:
  - [ ] Gradient: `linear-gradient(135deg, #7C3AED, #6366F1)`
  - [ ] Border-radius 12px
  - [ ] Hover: `scale(1.03)` + violet glow shadow
  - [ ] Loading: shimmer gradient animation + spinner

### Layout — Agent Pipeline (3 Cards)
- [ ] Build 3 glassmorphic agent status cards (horizontal row on desktop, vertical on mobile):
  - [ ] Glass surface: `rgba(30,41,59,0.6)` + `backdrop-filter: blur(12px)` + subtle border
  - [ ] Card anatomy: agent icon (32×32px) | agent name | status badge | output preview | metadata
- [ ] Implement 3 visual states per card:
  - [ ] **Idle**: muted border, greyed icon, no animation
  - [ ] **Running**: pulsing violet border (300ms ease-in-out), spinning loader, amber badge
  - [ ] **Complete**: green border flash → settle (500ms ease-out), checkmark icon, green badge
- [ ] Use `st.status()` (Streamlit 1.28+) for real-time running indicators
- [ ] Use `st.expander()` for intermediate output (Agent 1 URLs, Agent 2 facts) — collapsed by default

### Layout — Progress Timeline
- [ ] Vertical step indicator (desktop) / horizontal top bar (mobile):
  - [ ] Steps: 🔍 Search → 📄 Extract → ✍️ Write
  - [ ] Connecting line fills with violet as each agent completes

### Layout — Report Output Panel
- [ ] Full-width glassmorphic panel below agent cards
- [ ] "Research Report" header + copy-to-clipboard icon button
- [ ] Render final report with `st.markdown()`:
  - [ ] Smooth reveal: fade-in + Y+20 translate over 400ms `cubic-bezier(0.16,1,0.3,1)`
- [ ] Source URLs as clickable chips at the bottom
- [ ] `st.code()` block for raw markdown with native copy icon

### Responsive Behaviour
- [ ] Agent cards stack vertically on `<768px` screens
- [ ] Font sizes scale down ~15% on mobile
- [ ] Copy button becomes fixed bottom bar on mobile report section

---

## PHASE 7 — Observability (LangSmith)
> Tech Stack §7

- [ ] Set env vars: `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`
- [ ] Verify traces appear in LangSmith dashboard after a full pipeline run
- [ ] Capture screenshot of LangSmith trace showing all 3 agent steps, token counts, latencies
- [ ] Save screenshot to `docs/langsmith_trace.png` for README

---

## PHASE 8 — Testing & Quality
> PRD §6 (Success Metrics) | PRD §7 (Risk Mitigations)

- [ ] Run full end-to-end pipeline on **10 different topics** without crashing
- [ ] Verify each report has all 5 sections (Exec Summary, Key Findings, Analysis, Conclusion, References)
- [ ] Human relevance evaluation — score each report ≥ 8/10
- [ ] Test graceful degradation:
  - [ ] Test with an inaccessible URL — confirm it skips and continues (no crash)
  - [ ] Test with Groq 429 error — confirm exponential backoff kicks in
  - [ ] Test agent retry loop — confirm max_iterations cap prevents infinite loop
- [ ] Confirm API keys never appear in logs, console, or UI
- [ ] Test on desktop and tablet screen sizes
- [ ] Share public URL with ≥ 3 peers for feedback

---

## PHASE 9 — Deployment (Streamlit Community Cloud)
> PRD §4 (Non-Functional) | Tech Stack §8

- [ ] Push project to GitHub (public repo)
- [ ] Write `README.md` scaffold (placeholder, full content in Phase 10)
- [ ] Connect GitHub repo to Streamlit Community Cloud
- [ ] Set secrets in Streamlit dashboard: `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`
- [ ] Trigger first cloud deploy and verify public URL is live
- [ ] Confirm pipeline runs end-to-end at the public URL

---

## PHASE 10 — GitHub README & Portfolio Assets
> PRD §1.3 | PRD §5 Phase 4

- [ ] Create `docs/architecture.png` — system architecture diagram showing all 4 layers:
  - [ ] UI Layer (Streamlit) → Orchestration Layer (LangGraph + LangSmith) → Agent Layer (3 nodes) → Data Layer (StateDict)
- [ ] Record demo GIF (`docs/demo.gif`) showing full pipeline run in Streamlit UI
- [ ] Write immaculate `README.md` including:
  - [ ] Project banner with gradient background and MARS logo
  - [ ] One-paragraph executive summary
  - [ ] Architecture diagram embed
  - [ ] Feature list (3 agents, LangGraph, LangSmith tracing, Streamlit UI)
  - [ ] Tech stack badge row (LangGraph, Groq, Tavily, Streamlit, LangSmith)
  - [ ] Demo GIF embed
  - [ ] LangSmith trace screenshot
  - [ ] Quickstart instructions (`git clone`, `pip install`, `.env` setup, `streamlit run app.py`)
  - [ ] Public Streamlit URL button
  - [ ] Blog post link (once published)
- [ ] Get README feedback from ≥ 3 peers

---

## PHASE 11 — Blog Post (Medium / Dev.to)
> PRD §1.3 | PRD §5 Phase 5

- [ ] Outline article structure:
  - [ ] Why multi-agent systems? (problem statement)
  - [ ] Architecture walkthrough (LangGraph graph, state passing)
  - [ ] Key engineering challenges (Groq rate limits, URL failures, no-hallucination grounding)
  - [ ] LangSmith observability in practice
  - [ ] Design decisions (why LangGraph over CrewAI/AutoGen, why Groq over OpenAI)
  - [ ] Demo + public URL
- [ ] Write and publish on Medium or Dev.to
- [ ] Link blog post from GitHub README

---

## PHASE 12 — v2 Roadmap (Post-MVP)
> PRD §1.4 (Non-Goals for v1)

- [ ] **Streaming Output** — real-time partial agent output in Streamlit using `st.write_stream()`
- [ ] **User Auth + Report History** — saved sessions with login
- [ ] **PDF Export** — `weasyprint` or `pdfkit` for one-click PDF download
- [ ] **Image/Video Content Support** — multimodal extraction pipeline
- [ ] **ChromaDB RAG Integration** — vector store for large corpus (>50 URLs)
- [ ] **React + Framer Motion UI Upgrade** — full design doc vision (v2 frontend)
- [ ] **Parallel Agent Execution** — run Extractor on multiple URLs concurrently with `asyncio`

---

## Quick Reference — Design System Tokens
> Design Doc §8 | Apply in Streamlit CSS injection

| Token | Value |
|---|---|
| `--color-bg` | `#0F172A` |
| `--color-surface` | `#1E293B` |
| `--color-primary` | `#7C3AED` |
| `--color-primary-light` | `#A78BFA` |
| `--color-accent` | `#6366F1` |
| `--color-text` | `#F8FAFC` |
| `--color-text-muted` | `#94A3B8` |
| `--color-success` | `#10B981` |
| `--color-warning` | `#F59E0B` |
| `--color-error` | `#EF4444` |
| `--radius-card` | `16px` |
| `--radius-btn` | `12px` |
| `--blur-glass` | `12px` |
| `--transition-default` | `200ms ease-out` |

---

## Timeline Summary
| Phase | Deliverable | Target |
|---|---|---|
| Phase 1 | Project setup | Pre-Week 1 |
| Phase 2–4 | All 3 agent logic (CLI) | Week 1 |
| Phase 5 | Orchestrator + LangGraph pipeline | Week 2 |
| Phase 6 | Streamlit UI | Week 3 |
| Phase 7–9 | Observability + Testing + Deploy | Week 3–4 |
| Phase 10 | GitHub README + portfolio assets | Week 4 |
| Phase 11 | Blog post | Week 5 |
| Phase 12 | v2 features | Post-MVP |
