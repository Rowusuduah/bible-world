"""
context-lens RAG pipeline audit example.

This is the most common real-world use case: you have a RAG system that retrieves
documents and builds a long context. You want to know if your LLM reliably uses
information from ALL retrieved chunks — not just the first and last ones.

Problem: RAG pipelines retrieve 5-20 chunks. The LLM sees them in order.
If critical information is in chunk 4 of 10, it may be silently ignored.
You won't know until users complain.

context-lens tests this BEFORE you ship.

Run:
    python examples/rag_pipeline_audit.py --mock
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from context_lens import ContextLens, Needle, HaystackTemplate


# Simulate a RAG haystack: realistic document chunks
RAG_FILLER_CHUNK = """
This document describes our product catalog management system. Products are organized
into categories with hierarchical tags. Each product has a SKU, name, description,
price, and inventory count. The catalog supports bulk import via CSV with validation.
All prices are in USD and must be positive values. Out-of-stock items retain their
SKU but show availability=false in the API response.
"""


def make_rag_example_needles():
    """Realistic RAG needles — things that must be found across a long document context."""
    return [
        Needle(
            label="Rate limit policy",
            content="The API enforces a rate limit of 1000 requests per minute per API key.",
            question="What is the API rate limit?",
            expected_answer="1000 requests per minute per API key",
            answer_keywords=["1000", "per minute"],
        ),
        Needle(
            label="Error code 429 handling",
            content="When receiving error code 429, clients must implement exponential backoff starting at 2 seconds.",
            question="How should clients handle a 429 error code?",
            expected_answer="exponential backoff starting at 2 seconds",
            answer_keywords=["exponential backoff", "2 seconds"],
        ),
        Needle(
            label="Pagination token format",
            content="Pagination tokens expire after 24 hours and must be URL-encoded before use.",
            question="How long do pagination tokens last and how should they be encoded?",
            expected_answer="24 hours, URL-encoded",
            answer_keywords=["24 hours", "URL-encoded"],
        ),
    ]


def make_mock_fn_rag(needle_keywords_by_position: dict):
    """
    Simulated RAG LLM that has the classic middle-degradation problem.
    Correctly answers for needles at positions 0-1 and 8-9 (out of 10),
    but misses needles at positions 2-7 (the middle).
    """
    call_count = [0]
    total_positions = 10

    def mock_fn(prompt: str) -> str:
        call_count[0] += 1
        pos_idx = (call_count[0] - 1) % total_positions
        frac = pos_idx / (total_positions - 1)

        # Find which keywords are expected (check if any are in the prompt's needle section)
        for keywords in needle_keywords_by_position.values():
            # Check if this needle's content is in the prompt
            for kw in keywords:
                # Simulate retrieval: works at edges, fails in middle
                if frac <= 0.15 or frac >= 0.85:
                    return f"Based on the context: the answer contains {' and '.join(keywords)}."
                elif 0.15 < frac < 0.40 or 0.60 < frac < 0.85:
                    return f"Partially found: {keywords[0]} is mentioned."
                else:
                    return "I cannot find specific information about this in the provided context."

        return "No relevant information found in the provided context."

    return mock_fn


def run_rag_audit(mock: bool = True):
    print("\n" + "=" * 70)
    print("  context-lens — RAG Pipeline Context Position Audit")
    print("=" * 70)
    print()
    print("Scenario: RAG system builds a long context from 10+ retrieved chunks.")
    print("Question: Does the LLM reliably use information from ALL chunk positions?")
    print()

    needles = make_rag_example_needles()

    # RAG-style haystack: documents are concatenated
    haystack = HaystackTemplate(
        filler_text=RAG_FILLER_CHUNK,
        target_tokens=3000,
        tokens_per_filler=100,
        system_prompt=(
            "You are a technical documentation assistant. "
            "Answer the question using only the information in the provided documents. "
            "Be specific and quote the relevant details."
        ),
    )

    if mock:
        # Create a mock that shows middle-degradation pattern
        keyword_map = {n.label: n.answer_keywords for n in needles}
        model_fn = make_mock_fn_rag(keyword_map)
        model_name = "mock-rag-model (simulates lost-in-the-middle)"
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Set ANTHROPIC_API_KEY or use --mock flag.")
            sys.exit(1)
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        def model_fn(prompt: str) -> str:
            resp = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
        model_name = "claude-3-5-haiku-20241022"

    lens = ContextLens(
        model_fn=model_fn,
        model_name=model_name,
        reliable_threshold=0.85,
        conditional_threshold=0.65,
        db_path=".context_lens_rag.db",
    )

    # Run multi-needle audit
    heatmaps = lens.audit_multi(needles, haystack, positions=10, verbose=True)

    # Print individual reports
    for hm in heatmaps:
        hm.report(verbose=False)

    # Aggregate summary
    summary = lens.summary_report(heatmaps)
    print("\n" + "=" * 70)
    print("  AGGREGATE SUMMARY")
    print("=" * 70)
    print(f"  Needles tested  : {summary['needles_tested']}")
    print(f"  Overall score   : {summary['overall_score']:.1%}")
    print(f"  Overall verdict : {summary['overall_verdict']}")
    print()
    for n in summary["per_needle"]:
        icon = "[OK]" if n["verdict"] == "RELIABLE" else "[!]"
        print(f"  {icon} {n['label']:35} {n['score']:.1%}  {n['verdict']}")
        if n["fault_zones"]:
            print(f"       Fault zones: {[f'{z:.2f}' for z in n['fault_zones']]}")

    # CI gate
    passed, message = lens.ci_gate(heatmaps, min_score=0.80)
    print(f"\n  CI Gate: {message}")

    if not passed:
        print()
        print("  RECOMMENDATION: Before shipping this RAG configuration, audit which")
        print("  chunk positions consistently fail retrieval. Consider reordering retrieved")
        print("  chunks, adding chunk recency/relevance emphasis, or reducing total chunks.")

    return summary


if __name__ == "__main__":
    mock = "--mock" in sys.argv or True  # Default to mock for easy running
    run_rag_audit(mock=mock)
