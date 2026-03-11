"""
MARS — agents/writer.py
Agent 3: Report Writer

Accepts the extracted facts dict from the Extractor and synthesises a
publication-ready markdown report. Every claim is grounded in extracted facts —
no hallucination.

LangGraph node: write_node(state) -> state
"""

import logging
import time
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


# ── Prompt building ────────────────────────────────────────────────────────────

def _build_facts_block(extracted_facts: dict[str, list[str]]) -> str:
    """Format the extracted facts dict as a readable source block for the LLM."""
    blocks = []
    for url, facts in extracted_facts.items():
        if not facts:
            continue
        fact_lines = "\n".join(f"  - {f}" for f in facts)
        blocks.append(f"SOURCE: {url}\n{fact_lines}")
    return "\n\n".join(blocks)


_SYSTEM_PROMPT = """You are an expert research report writer. Your task is to synthesize 
provided facts into a clear, professional, publication-ready markdown report.

STRICT RULES (non-negotiable):
1. ONLY use information from the provided facts — do NOT add any knowledge from training data
2. Every claim must trace back to a source provided
3. Do NOT hallucinate statistics, dates, names, or claims
4. If facts are insufficient for a section, write "Insufficient data available."
5. Write in formal, professional prose — no bullet points in main body
6. References section must list all source URLs as numbered markdown links

REQUIRED REPORT STRUCTURE (use exactly these headings):
# [Topic] — Research Report

## Executive Summary
(2–3 sentence overview of what the research found)

## Key Findings
(3–6 most important discoveries, as a numbered list)

## Detailed Analysis
(3–5 paragraphs of in-depth analysis drawing from the facts)

## Conclusion
(1–2 paragraph synthesis and takeaway)

## References
(numbered list of all source URLs used)
"""


# ── Core writer logic ─────────────────────────────────────────────────────────

def _generate_report(topic: str, facts_block: str) -> str:
    """Call ChatGroq to generate the markdown report."""
    llm = ChatGroq(
        model=config.LLM_MODEL,
        temperature=0.5,
        api_key=config.GROQ_API_KEY,
    )

    user_prompt = (
        f"Research Topic: {topic}\n\n"
        f"EXTRACTED FACTS (use ONLY these):\n\n{facts_block}\n\n"
        "Write the full research report now."
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    attempt = 0
    while attempt < config.MAX_RETRIES:
        try:
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as exc:
            wait = config.BACKOFF_BASE_SECONDS * (2 ** attempt)
            if "429" in str(exc):
                logger.warning(f"[Writer] Rate limit hit — waiting {wait}s.")
                time.sleep(wait)
            else:
                logger.error(f"[Writer] LLM error on attempt {attempt + 1}: {exc}")
            attempt += 1

    return f"# {topic} — Research Report\n\n⚠️ Report generation failed after {config.MAX_RETRIES} attempts."


# ── LangGraph node ─────────────────────────────────────────────────────────────

def write_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node — Report Writer.

    Input state keys:  extracted_facts (dict), topic (str)
    Output state keys: report (str), error (str | None)
    """
    topic: str = state.get("topic", "Unknown Topic")
    extracted_facts: dict[str, list[str]] = state.get("extracted_facts", {})

    logger.info(f"[Writer] ▶  Generating report for: '{topic}'")

    if not extracted_facts:
        fallback = (
            f"# {topic} — Research Report\n\n"
            "⚠️ **No facts could be extracted from the search results.** "
            "Please try a different topic or check your API keys."
        )
        state["report"] = fallback
        state["error"] = "No extracted facts available for Writer agent."
        logger.warning("[Writer] No facts available — returning fallback report.")
        return state

    facts_block = _build_facts_block(extracted_facts)
    fact_count = sum(len(f) for f in extracted_facts.values())
    src_count = len(extracted_facts)
    logger.info(f"[Writer] Synthesising {fact_count} facts from {src_count} sources.")

    report = _generate_report(topic, facts_block)

    state["report"] = report
    state["error"] = None
    logger.info(f"[Writer] ✓  Report generated. Length: {len(report)} chars.")
    return state


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    missing = config.validate_keys()
    if missing:
        print(f"❌ Missing API keys: {missing}. Check your .env file.")
        exit(1)

    # Sample state with pre-seeded facts
    sample_state = {
        "topic": "LangGraph multi-agent AI systems",
        "extracted_facts": {
            "https://langchain-ai.github.io/langgraph/": [
                "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
                "LangGraph uses a graph-based DAG where nodes are agent functions and edges define execution flow.",
                "LangGraph v1.0 was released in late 2025 and is now considered production-ready.",
                "LangGraph supports human-in-the-loop interactions as a first-class feature.",
            ],
            "https://blog.langchain.dev/langgraph-multi-agent/": [
                "Multi-agent systems with LangGraph allow specialised agents to collaborate on complex tasks.",
                "State is passed as a typed dictionary between nodes, ensuring type safety.",
                "LangSmith provides full observability for LangGraph pipelines including token usage and latency.",
            ],
        },
    }

    result = write_node(sample_state)
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
    print("\n" + "=" * 60)
    print(result["report"])
