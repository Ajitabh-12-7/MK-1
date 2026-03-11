"""
MARS — agents/searcher.py
Agent 1: Web Searcher

Accepts a topic string, runs a Tavily web search, filters results, and returns
a structured list of {title, url, snippet} objects — max 10 results.

LangGraph node: search_node(state) -> state
"""

import json
import logging
import time
from typing import Any

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

# ── LLM & Tool setup ──────────────────────────────────────────────────────────

def _build_llm() -> ChatGroq:
    return ChatGroq(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        api_key=config.GROQ_API_KEY,
    )


def _build_search_tool() -> TavilySearchResults:
    return TavilySearchResults(
        max_results=config.SEARCH_MAX_RESULTS,
        api_key=config.TAVILY_API_KEY,
        include_answer=False,
        include_raw_content=False,
    )


# ── Core search logic ─────────────────────────────────────────────────────────

def _run_search(topic: str) -> list[dict]:
    """Execute Tavily search and return raw results list."""
    tool = _build_search_tool()
    raw = tool.invoke({"query": topic})

    # Tavily returns a list of dicts with keys: url, content, title, score
    results = []
    seen_urls: set[str] = set()

    for item in raw:
        url = item.get("url", "")
        title = item.get("title", "No title")
        snippet = item.get("content", "")

        # Filter duplicates
        if url in seen_urls or not url:
            continue
        seen_urls.add(url)

        # Filter out non-useful results (empty snippets)
        if not snippet.strip():
            logger.warning(f"[Searcher] Skipping result with empty snippet: {url}")
            continue

        results.append({"title": title, "url": url, "snippet": snippet})

    logger.info(f"[Searcher] Found {len(results)} valid results for topic: '{topic}'")
    return results[: config.SEARCH_MAX_RESULTS]


def _refine_query_with_llm(topic: str) -> str:
    """Use LLM to produce an optimised search query for the given topic."""
    llm = _build_llm()
    messages = [
        SystemMessage(
            content=(
                "You are a research assistant. Given a user topic, produce a concise, "
                "specific web search query that will yield the most informative results. "
                "Return ONLY the query string — no explanation, no quotes."
            )
        ),
        HumanMessage(content=f"Topic: {topic}"),
    ]
    response = llm.invoke(messages)
    refined = response.content.strip()
    logger.info(f"[Searcher] Refined query: '{refined}'")
    return refined


# ── LangGraph node ──────────────────────────────────────────────────────────────

def search_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node — Web Searcher.

    Input state keys:  topic (str)
    Output state keys: search_results (list[dict]), error (str | None)
    """
    topic: str = state.get("topic", "")
    logger.info(f"[Searcher] ▶  Starting search for: '{topic}'")

    if not topic.strip():
        state["error"] = "No topic provided to Searcher agent."
        state["search_results"] = []
        return state

    attempt = 0
    while attempt < config.MAX_RETRIES:
        try:
            # Optionally refine the query with the LLM
            refined_query = _refine_query_with_llm(topic)
            results = _run_search(refined_query)

            if not results:
                logger.warning("[Searcher] No results found — retrying with original topic.")
                results = _run_search(topic)

            state["search_results"] = results
            state["error"] = None
            logger.info(f"[Searcher] ✓  Done. {len(results)} results returned.")
            return state

        except Exception as exc:
            wait = config.BACKOFF_BASE_SECONDS * (2 ** attempt)
            if "429" in str(exc):
                logger.warning(f"[Searcher] Rate limit hit — waiting {wait}s before retry.")
                time.sleep(wait)
            else:
                logger.error(f"[Searcher] Error on attempt {attempt + 1}: {exc}")
            attempt += 1

    # All retries failed
    state["error"] = f"Searcher agent failed after {config.MAX_RETRIES} attempts."
    state["search_results"] = []
    return state


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    missing = config.validate_keys()
    if missing:
        print(f"❌ Missing API keys: {missing}. Check your .env file.")
        exit(1)

    test_topic = input("Enter a research topic: ").strip() or "LangGraph multi-agent systems"
    result_state = search_node({"topic": test_topic})

    if result_state.get("error"):
        print(f"\n❌ Error: {result_state['error']}")
    else:
        print(f"\n✅ {len(result_state['search_results'])} results:\n")
        print(json.dumps(result_state["search_results"], indent=2))
