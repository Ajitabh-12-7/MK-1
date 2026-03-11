"""
MARS — tests/test_pipeline.py
End-to-end and unit tests for the pipeline.

Run: python -m pytest tests/ -v
  or: python tests/test_pipeline.py (quick smoke test)
"""

import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

# ── Unit: Config validation ────────────────────────────────────────────────────

def test_config_loads():
    """Config module must import without error."""
    assert hasattr(config, "GROQ_API_KEY")
    assert hasattr(config, "TAVILY_API_KEY")
    assert hasattr(config, "LLM_MODEL")
    assert config.LLM_MODEL == "llama-3.3-70b-versatile"
    print("✅ test_config_loads passed")


def test_validate_keys_returns_list():
    """validate_keys must return a list."""
    result = config.validate_keys()
    assert isinstance(result, list)
    print(f"✅ test_validate_keys_returns_list passed (missing: {result})")


# ── Unit: Extractor HTML parsing ───────────────────────────────────────────────

def test_html_parsing():
    """BS4 parser must extract meaningful text from sample HTML."""
    from agents.extractor import _parse_html
    sample_html = """
    <html><body>
    <nav>Navigation menu here</nav>
    <article>
        <p>LangGraph is a library for building stateful multi-actor applications.</p>
        <p>It uses a graph-based DAG where nodes represent agents.</p>
        <p>Version 1.0 was released in late 2025.</p>
    </article>
    <footer>Footer content</footer>
    </body></html>
    """
    text = _parse_html(sample_html)
    assert "LangGraph" in text
    assert "DAG" in text
    assert "Navigation" not in text  # nav should be stripped
    assert "Footer" not in text       # footer should be stripped
    print(f"✅ test_html_parsing passed. Extracted {len(text)} chars.")


# ── Unit: Facts block builder ──────────────────────────────────────────────────

def test_facts_block_builder():
    """Writer facts block must format all facts."""
    from agents.writer import _build_facts_block
    facts = {
        "https://example.com/a": ["Fact one.", "Fact two."],
        "https://example.com/b": ["Fact three."],
    }
    block = _build_facts_block(facts)
    assert "example.com/a" in block
    assert "Fact one." in block
    assert "Fact three." in block
    print("✅ test_facts_block_builder passed")


# ── Integration: Search node (requires TAVILY_API_KEY) ─────────────────────────

def test_search_node_integration():
    """Search node must return at least 1 result for a known topic."""
    if "TAVILY_API_KEY" in config.validate_keys():
        print("⚠️  Skipping test_search_node_integration — TAVILY_API_KEY not set")
        return

    from agents.searcher import search_node
    state = search_node({"topic": "Python async programming best practices"})

    assert state.get("error") is None or state.get("search_results"), "Search failed with no results"
    results = state.get("search_results", [])
    assert len(results) > 0, "Search returned 0 results"
    assert all("url" in r for r in results), "Results missing url field"
    assert all("title" in r for r in results), "Results missing title field"
    print(f"✅ test_search_node_integration passed. {len(results)} results.")


# ── Integration: Full pipeline (requires all API keys) ─────────────────────────

def test_full_pipeline_smoke():
    """Full pipeline must run end-to-end without crashing."""
    missing = config.validate_keys()
    if missing:
        print(f"⚠️  Skipping test_full_pipeline_smoke — missing keys: {missing}")
        return

    from orchestrator import run_pipeline
    result = run_pipeline("Python asyncio event loop 2025")

    assert "topic" in result
    assert "report" in result
    assert len(result.get("report", "")) > 100, "Report is too short"
    print(f"✅ test_full_pipeline_smoke passed. Report: {len(result['report'])} chars.")


# ── Resilience: Graceful degradation ──────────────────────────────────────────

def test_extract_node_skips_bad_url():
    """Extractor must skip inaccessible URLs gracefully without crashing."""
    from agents.extractor import extract_node
    state = {
        "topic": "test topic",
        "search_results": [
            {"title": "Bad URL", "url": "https://this-url-definitely-does-not-exist-12345.xyz/", "snippet": "test"},
        ],
    }
    result = extract_node(state)
    # Should not crash, extracted_facts may be empty but no exception
    assert "extracted_facts" in result
    print("✅ test_extract_node_skips_bad_url passed")


def test_write_node_with_empty_facts():
    """Writer must return a fallback report when no facts are available."""
    from agents.writer import write_node
    state = {"topic": "something", "extracted_facts": {}}
    result = write_node(state)
    assert "report" in result
    assert len(result["report"]) > 0
    print("✅ test_write_node_with_empty_facts passed")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MARS — Test Suite")
    print("=" * 60 + "\n")

    tests = [
        test_config_loads,
        test_validate_keys_returns_list,
        test_html_parsing,
        test_facts_block_builder,
        test_extract_node_skips_bad_url,
        test_write_node_with_empty_facts,
        test_search_node_integration,
        test_full_pipeline_smoke,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
