"""
MARS — agents/extractor.py
Agent 2: Content Extractor

For each URL from the Searcher:
  1. Fetch full-text HTML with httpx (async-style, sync wrapper)
  2. Fall back to Playwright for JS-heavy pages
  3. Parse with BeautifulSoup4
  4. Use ChatGroq to extract key facts attributed to source URLs

LangGraph node: extract_node(state) -> state
"""

import asyncio
import logging
import re
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

# ── HTML Fetching ─────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_with_httpx(url: str) -> str | None:
    """Fetch page HTML using httpx (synchronous). Returns None on failure."""
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=config.HTTP_TIMEOUT,
            headers=_HEADERS,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        logger.warning(f"[Extractor] httpx failed for {url}: {exc}")
        return None


async def _fetch_with_playwright(url: str) -> str | None:
    """Playwright fallback for JS-heavy pages."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=int(config.HTTP_TIMEOUT * 1000 * 3))
            await page.wait_for_load_state("domcontentloaded")
            html = await page.content()
            await browser.close()
            return html
    except Exception as exc:
        logger.warning(f"[Extractor] Playwright failed for {url}: {exc}")
        return None


def fetch_url(url: str) -> str | None:
    """
    Fetch and return clean text from a URL.
    Uses httpx first; falls back to Playwright for JS-heavy pages.
    Returns None if both fail.
    """
    html = _fetch_with_httpx(url)

    # If content is missing or too short, try Playwright
    if html is None or len(html.strip()) < config.MIN_TEXT_LENGTH:
        logger.info(f"[Extractor] Trying Playwright fallback for: {url}")
        try:
            loop = asyncio.new_event_loop()
            html = loop.run_until_complete(_fetch_with_playwright(url))
            loop.close()
        except Exception as exc:
            logger.warning(f"[Extractor] Playwright fallback error: {exc}")
            return None

    return html


# ── HTML Parsing ──────────────────────────────────────────────────────────────

def _parse_html(html: str) -> str:
    """Extract clean readable text from HTML using BeautifulSoup4."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()

    # Try to find the main content container first
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|main|article", re.I))
        or soup.find(class_=re.compile(r"content|main|article|post|entry", re.I))
        or soup.body
    )

    if main is None:
        return soup.get_text(separator=" ", strip=True)

    # Extract paragraphs
    paragraphs = main.find_all("p")
    text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(strip=True))

    # Fallback — get all text from main container
    if len(text) < config.MIN_TEXT_LENGTH:
        text = main.get_text(separator=" ", strip=True)

    # Clean up whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text[:8000]  # Cap to ~8k chars to stay within LLM context


# ── Fact Extraction (LLM) ─────────────────────────────────────────────────────

def _extract_facts_llm(url: str, text: str, topic: str) -> list[str]:
    """Use ChatGroq to extract key facts from page text."""
    llm = ChatGroq(
        model=config.LLM_MODEL,
        temperature=0.2,  # low temp for factual extraction
        api_key=config.GROQ_API_KEY,
    )

    system_prompt = (
        "You are a precise research assistant. Extract key facts, statistics, and claims "
        "from the provided text that are relevant to the research topic. "
        "Rules:\n"
        "- Return ONLY a numbered list of facts (1. fact, 2. fact, ...)\n"
        "- Each fact must be a complete, standalone sentence\n"
        "- Include specific numbers, dates, names when present\n"
        "- Do NOT include opinions or marketing language\n"
        "- Extract 5–10 most important facts only\n"
        "- If text is irrelevant or empty, return: NO_FACTS"
    )

    user_prompt = f"Research Topic: {topic}\n\nSource URL: {url}\n\nPage Text:\n{text}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw == "NO_FACTS" or not raw:
            return []

        # Parse numbered list into fact strings
        facts = []
        for line in raw.splitlines():
            line = line.strip()
            if line and re.match(r"^\d+\.", line):
                fact = re.sub(r"^\d+\.\s*", "", line).strip()
                if fact:
                    facts.append(fact)

        return facts

    except Exception as exc:
        logger.error(f"[Extractor] LLM fact extraction failed for {url}: {exc}")
        return []


# ── LangGraph node ──────────────────────────────────────────────────────────────

def extract_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node — Content Extractor.

    Input state keys:  search_results (list[dict{title, url, snippet}]), topic
    Output state keys: extracted_facts (dict{url: list[str]}), error (str | None)
    """
    search_results: list[dict] = state.get("search_results", [])
    topic: str = state.get("topic", "")
    logger.info(f"[Extractor] ▶  Extracting facts from {len(search_results)} URLs.")

    if not search_results:
        state["error"] = "No search results to extract from."
        state["extracted_facts"] = {}
        return state

    extracted_facts: dict[str, list[str]] = {}
    llm_call_count = 0

    for idx, result in enumerate(search_results):
        url = result.get("url", "")
        if not url:
            continue

        logger.info(f"[Extractor] [{idx + 1}/{len(search_results)}] Processing: {url}")

        # Fetch and parse HTML
        html = fetch_url(url)
        if html is None:
            logger.warning(f"[Extractor] Skipping {url} — could not fetch content.")
            continue

        text = _parse_html(html)
        if not text or len(text) < config.MIN_TEXT_LENGTH:
            logger.warning(f"[Extractor] Skipping {url} — insufficient text after parsing.")
            continue

        # Rate limit guard before each LLM call
        if llm_call_count > 0:
            time.sleep(config.AGENT_SLEEP_SECONDS)

        facts = _extract_facts_llm(url, text, topic)
        llm_call_count += 1

        if facts:
            extracted_facts[url] = facts
            logger.info(f"[Extractor]   ✓  {len(facts)} facts extracted.")
        else:
            logger.warning(f"[Extractor]   ⚠  No facts extracted from: {url}")

    state["extracted_facts"] = extracted_facts
    state["error"] = None if extracted_facts else "No facts could be extracted from any URL."
    logger.info(
        f"[Extractor] ✓  Done. Facts from {len(extracted_facts)} / {len(search_results)} URLs."
    )
    return state


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    missing = config.validate_keys()
    if missing:
        print(f"❌ Missing API keys: {missing}. Check your .env file.")
        exit(1)

    # Quick test with a sample state
    sample_state = {
        "topic": "LangGraph multi-agent systems",
        "search_results": [
            {
                "title": "LangGraph Overview",
                "url": "https://langchain-ai.github.io/langgraph/",
                "snippet": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
            }
        ],
    }

    result = extract_node(sample_state)
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
    else:
        print(f"\n✅ Extracted facts:\n")
        print(json.dumps(result["extracted_facts"], indent=2))
