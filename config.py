"""
MARS — config.py
Centralised configuration and environment loading.
All modules import from here — never use os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent
load_dotenv(_ROOT / ".env", override=False)

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")

# ── LangSmith Tracing ──────────────────────────────────────────────────────────
LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_ENDPOINT: str = os.getenv(
    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
)
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "MARS-MultiAgent-Research")

# ── LLM Configuration ─────────────────────────────────────────────────────────
LLM_MODEL: str = "llama-3.3-70b-versatile"
LLM_TEMPERATURE: float = 0.7

# ── Search Configuration ──────────────────────────────────────────────────────
SEARCH_MAX_RESULTS: int = 10

# ── Scraping Configuration ────────────────────────────────────────────────────
HTTP_TIMEOUT: float = 10.0          # seconds per URL fetch
MIN_TEXT_LENGTH: int = 200          # chars — below this triggers Playwright fallback

# ── Rate limit guard (Groq free tier: 30 RPM) ────────────────────────────────
AGENT_SLEEP_SECONDS: float = 2.0
MAX_RETRIES: int = 3
BACKOFF_BASE_SECONDS: float = 4.0  # doubles on each 429

# ── Pipeline limits ───────────────────────────────────────────────────────────
MAX_PIPELINE_ITERATIONS: int = 3

# ── Validation ────────────────────────────────────────────────────────────────
def validate_keys() -> list[str]:
    """Return list of missing required API key names."""
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    return missing
