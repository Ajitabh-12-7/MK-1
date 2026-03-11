<div align="center">

# 🔭 MARS — Multi-Agent Research System

**Autonomous AI Team for Deep Research & Report Generation**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.x-7C3AED?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-10B981?style=for-the-badge)](https://console.groq.com)
[![Tavily](https://img.shields.io/badge/Tavily-Search-6366F1?style=for-the-badge)](https://tavily.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-EF4444?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangSmith](https://img.shields.io/badge/LangSmith-Tracing-F59E0B?style=for-the-badge)](https://smith.langchain.com)

*Enter a topic. Three AI agents search the web, extract facts, and write a publication-ready report — automatically.*

**[🚀 Live Demo](https://your-app.streamlit.app)**  ·  **[📝 Blog Post](#)**  ·  **[📊 LangSmith Traces](#)**

</div>

---

## What is MARS?

MARS orchestrates a team of three specialised AI agents in a sequential pipeline:

```
User Topic → [Agent 1: Searcher] → [Agent 2: Extractor] → [Agent 3: Writer] → Report
```

| Agent | Tool | Job |
|---|---|---|
| 🔍 **Web Searcher** | Tavily API + Groq LLM | Searches the web, refines query, returns top 10 sources |
| 📄 **Content Extractor** | httpx + BeautifulSoup4 + Groq LLM | Fetches pages, parses HTML, extracts key facts |
| ✍️ **Report Writer** | Groq LLM (llama-3.3-70b) | Synthesises a grounded, citation-backed markdown report |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
│              Streamlit (app.py) — Dark Glassmorphic UI          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                  ORCHESTRATION LAYER                            │
│   LangGraph StateGraph  ──  search → extract → write → END     │
│   LangSmith ── traces every node: tokens, latency, errors      │
└──────────┬────────────────────┬────────────────────┬────────────┘
           │                    │                    │
┌──────────▼──────┐   ┌─────────▼──────┐   ┌────────▼───────────┐
│  AGENT 1        │   │  AGENT 2        │   │  AGENT 3           │
│  Web Searcher   │   │  Extractor      │   │  Report Writer     │
│  Tavily + Groq  │   │  httpx + BS4    │   │  Groq llama-3.3    │
└──────────┬──────┘   │  + Groq         │   └────────────────────┘
           │          └────────────────┘
┌──────────▼─────────────────────────────────────────────────────┐
│                     DATA LAYER                                 │
│      LangGraph AgentState TypedDict — passed between nodes     │
│      ChromaDB (v2) — optional vector store for large corpora   │
└─────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **LangGraph over CrewAI/AutoGen**: Graph-based state model maps directly to this sequential pipeline. LangSmith tracing proves it's production-grade.
- **Groq (free tier)** over OpenAI: `llama-3.3-70b-versatile` at 0 cost, ~300 tok/sec. One import swap from `ChatOpenAI`.
- **Tavily** over SerpAPI/DuckDuckGo: Built natively for LLM agents — returns clean structured snippets, not raw HTML.

---

## Quickstart

### 1. Clone
```bash
git clone https://github.com/yourusername/MARS-MultiAgent-Research.git
cd MARS-MultiAgent-Research
```

### 2. Virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium   # optional: for JS-heavy pages
```

### 4. Configure API keys
```bash
cp .env.example .env
# Edit .env and add your keys:
# GROQ_API_KEY      — https://console.groq.com/  (free)
# TAVILY_API_KEY    — https://app.tavily.com/     (free, 1K calls/mo)
# LANGCHAIN_API_KEY — https://smith.langchain.com (free)
```

### 5. Run
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## CLI Mode

Each agent can be tested independently:
```bash
# Test Searcher
python agents/searcher.py

# Test Extractor
python agents/extractor.py

# Test Writer
python agents/writer.py

# Run full pipeline on a topic
python orchestrator.py "LangGraph multi-agent systems 2025"
```

---

## Testing
```bash
# Full test suite
python tests/test_pipeline.py

# With pytest (if installed)
python -m pytest tests/ -v
```

---

## Deployment (Streamlit Community Cloud)

1. Push repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo → select `app.py`
4. Add secrets: `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`
5. Deploy — your public URL is live in ~60 seconds

---

## Tech Stack

| Category | Tool | Why |
|---|---|---|
| Agent Framework | LangGraph 0.2.x | Best state management for 3-node pipeline |
| LLM | Groq + llama-3.3-70b | Zero cost, ~300 tok/sec, OpenAI-compatible |
| Web Search | Tavily | Built for LLM agents, clean structured results |
| Web Scraping | httpx + BS4 + Playwright | Handles 90%+ of real-world URLs |
| UI | Streamlit 1.35+ | Fastest path to public live URL |
| Observability | LangSmith | Full trace: tokens, latency, agent steps |
| Hosting | Streamlit Community Cloud | Free, 24/7 public URL |

---

## Rate Limits

Groq free tier: 30 RPM. A `time.sleep(2)` guard is placed between each agent transition. On 429 errors → exponential backoff starting at 4s.

```python
# orchestrator.py
time.sleep(2)   # Between search → extract
time.sleep(2)   # Between extract → write
```

---

## Project Structure

```
MARS/
├── app.py                # Streamlit UI entry point
├── orchestrator.py       # LangGraph StateGraph pipeline
├── config.py             # Centralised env loading
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml       # Streamlit dark theme
├── agents/
│   ├── searcher.py       # Agent 1 — Web Searcher
│   ├── extractor.py      # Agent 2 — Content Extractor
│   └── writer.py         # Agent 3 — Report Writer
├── tests/
│   └── test_pipeline.py  # Unit + integration tests
└── docs/
    └── architecture.png  # System diagram
```

---

## Author

**Ajitabh Mishra (Dan)**
B.Tech CSE · Sharda University · 3rd Year · 2026

*This project is designed as a portfolio centrepiece for Generative AI, Agentic AI, and MLOps roles.*

---

<div align="center">
<sub>Built with LangGraph · Groq · Tavily · Streamlit · LangSmith</sub>
</div>
