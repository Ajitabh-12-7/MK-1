"""
MARS — orchestrator.py
LangGraph Pipeline Orchestrator

Defines AgentState, builds the StateGraph (search → extract → write),
and runs the full pipeline with rate limit guards, error handling, and logging.
"""

import logging
import sys
import time
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

import config
from agents.searcher import search_node
from agents.extractor import extract_node
from agents.writer import write_node

logger = logging.getLogger(__name__)

# ── State definition ──────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    """Typed state dictionary passed between LangGraph nodes."""
    topic: str                          # Input: research topic
    search_results: list[dict]          # Agent 1 output: [{title, url, snippet}]
    extracted_facts: dict[str, list]    # Agent 2 output: {url: [fact1, fact2, ...]}
    report: str                         # Agent 3 output: markdown report string
    error: str | None                   # Error message from any agent


# ── Rate-limit wrapped nodes ──────────────────────────────────────────────────

def _search_node_wrapped(state: AgentState) -> AgentState:
    logger.info("\n" + "=" * 60)
    logger.info("🔍  AGENT 1 — WEB SEARCHER  starting...")
    result = search_node(dict(state))
    logger.info("🔍  AGENT 1 — WEB SEARCHER  complete.")
    logger.info(f"    Results: {len(result.get('search_results', []))}")
    time.sleep(config.AGENT_SLEEP_SECONDS)   # Groq 30 RPM guard
    return result


def _extract_node_wrapped(state: AgentState) -> AgentState:
    logger.info("\n" + "=" * 60)
    logger.info("📄  AGENT 2 — CONTENT EXTRACTOR  starting...")
    result = extract_node(dict(state))
    logger.info("📄  AGENT 2 — CONTENT EXTRACTOR  complete.")
    src_count = len(result.get("extracted_facts", {}))
    logger.info(f"    Sources with facts: {src_count}")
    time.sleep(config.AGENT_SLEEP_SECONDS)   # Groq 30 RPM guard
    return result


def _write_node_wrapped(state: AgentState) -> AgentState:
    logger.info("\n" + "=" * 60)
    logger.info("✍️   AGENT 3 — REPORT WRITER  starting...")
    result = write_node(dict(state))
    logger.info("✍️   AGENT 3 — REPORT WRITER  complete.")
    report_len = len(result.get("report", ""))
    logger.info(f"    Report length: {report_len} chars")
    return result


# ── Graph construction ────────────────────────────────────────────────────────

def _build_graph() -> Any:
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("search", _search_node_wrapped)
    graph.add_node("extract", _extract_node_wrapped)
    graph.add_node("write", _write_node_wrapped)

    # Define edges — sequential pipeline
    graph.set_entry_point("search")
    graph.add_edge("search", "extract")
    graph.add_edge("extract", "write")
    graph.add_edge("write", END)

    return graph.compile()


# Singleton pipeline (compiled once, reused across Streamlit runs)
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = _build_graph()
    return _pipeline


# ── Public API ────────────────────────────────────────────────────────────────

def run_pipeline(topic: str) -> dict[str, Any]:
    """
    Run the full MARS pipeline for a given topic.

    Args:
        topic: The research topic string.

    Returns:
        Final AgentState dict with keys:
            - topic, search_results, extracted_facts, report, error
    """
    missing = config.validate_keys()
    if missing:
        return {
            "topic": topic,
            "error": f"Missing API keys: {missing}. Please check your .env file.",
            "report": "",
            "search_results": [],
            "extracted_facts": {},
        }

    initial_state: AgentState = {
        "topic": topic,
        "search_results": [],
        "extracted_facts": {},
        "report": "",
        "error": None,
    }

    logger.info(f"\n{'#' * 60}")
    logger.info(f"MARS Pipeline  |  Topic: {topic}")
    logger.info(f"{'#' * 60}")

    start_time = time.time()

    try:
        pipeline = _get_pipeline()
        result = pipeline.invoke(initial_state)
        elapsed = round(time.time() - start_time, 1)
        logger.info(f"\n✅  Pipeline complete in {elapsed}s")
        return dict(result)

    except Exception as exc:
        elapsed = round(time.time() - start_time, 1)
        logger.error(f"\n❌  Pipeline failed after {elapsed}s: {exc}", exc_info=True)
        return {
            "topic": topic,
            "error": f"Pipeline error: {str(exc)}",
            "report": f"# {topic} — Research Report\n\n⚠️ The pipeline encountered an unexpected error: {str(exc)}",
            "search_results": [],
            "extracted_facts": {},
        }


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter a research topic: ").strip()
        if not topic:
            topic = "LangGraph multi-agent AI systems 2025"

    result = run_pipeline(topic)

    print("\n" + "=" * 60)
    if result.get("error"):
        print(f"⚠️  Error: {result['error']}\n")

    print(result.get("report", "No report generated."))
    print("\n" + "=" * 60)
    print(f"Sources used: {len(result.get('extracted_facts', {}))}")
