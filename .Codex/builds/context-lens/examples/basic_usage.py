"""
context-lens basic usage example.

This example demonstrates the core workflow:
1. Define a Needle (a key fact that must be found in context)
2. Define a HaystackTemplate (the surrounding context)
3. Run a ContextLens audit across multiple positions
4. Read the PositionHeatmap result

Run this example:
    pip install context-lens anthropic
    export ANTHROPIC_API_KEY=your-key
    python examples/basic_usage.py

Or test without an API key using the mock model:
    python examples/basic_usage.py --mock
"""

import sys
import os

# Allow running from the examples/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from context_lens import ContextLens, Needle, HaystackTemplate


# ------------------------------------------------------------------
# Step 1: Define your model function
# ------------------------------------------------------------------
# This is YOUR LLM call. context-lens is provider-agnostic.
# Just wrap it in a function: str -> str.

def make_model_fn(mock: bool = False):
    """Build a model function for the example."""
    if mock:
        # Mock: always returns the needle content if it was in the first 20% or last 20%
        # (simulates the classic lost-in-the-middle problem for demonstration)
        print("[MOCK MODE] Using simulated LLM responses to demonstrate lost-in-the-middle pattern.")
        call_count = [0]
        def mock_fn(prompt: str) -> str:
            call_count[0] += 1
            pos = call_count[0]
            total = 10  # assume 10 positions
            # Simulate: model retrieves needle at positions 1-2 and 9-10, fails in middle
            frac = (pos - 1) / (total - 1) if total > 1 else 0
            if frac <= 0.22 or frac >= 0.78:
                return "The server configuration key is SERVER_CONFIG_KEY=prod-alpha-7."
            else:
                return "I don't see any specific configuration key mentioned in the provided context."
        return mock_fn

    # Real model: Anthropic Claude (swap for any provider)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set. Add --mock flag to use mock responses.")
        print("Usage: python examples/basic_usage.py --mock")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    def claude_fn(prompt: str) -> str:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    return claude_fn


# ------------------------------------------------------------------
# Step 2: Define your Needle
# ------------------------------------------------------------------
# A Needle is the critical piece of information that must be
# retrieved from wherever it appears in the context.

needle = Needle(
    label="Server configuration key",
    content="The server configuration key is SERVER_CONFIG_KEY=prod-alpha-7.",
    question="What is the server configuration key? Provide the exact value.",
    expected_answer="SERVER_CONFIG_KEY=prod-alpha-7",
    answer_keywords=["SERVER_CONFIG_KEY", "prod-alpha-7"],
)


# ------------------------------------------------------------------
# Step 3: Define your Haystack
# ------------------------------------------------------------------
# The haystack is the surrounding context the needle is embedded in.
# Use realistic filler text for your domain.

haystack = HaystackTemplate(
    filler_text=(
        "The following document contains operational procedures for the system. "
        "All services must be monitored at regular intervals. "
        "Engineers should follow the established runbook for incident response. "
        "Escalation paths are documented in the engineering handbook. "
    ),
    target_tokens=2000,     # Target context size in tokens
    tokens_per_filler=40,   # Approximate tokens in filler_text above
    system_prompt="You are a helpful assistant. Answer questions using only information from the provided context.",
)


# ------------------------------------------------------------------
# Step 4: Run the audit
# ------------------------------------------------------------------

def run_example(mock: bool = False):
    model_fn = make_model_fn(mock=mock)

    lens = ContextLens(
        model_fn=model_fn,
        model_name="claude-3-5-haiku-20241022" if not mock else "mock",
        reliable_threshold=0.90,
        conditional_threshold=0.70,
        db_path=".context_lens_example.db",
    )

    print("\n" + "=" * 60)
    print("  context-lens — Basic Usage Example")
    print("=" * 60)
    print(f"\nNeedle   : {needle.label}")
    print(f"Question : {needle.question}")
    print(f"Keywords : {needle.answer_keywords}")
    print(f"Positions: 10")
    print()

    # Run the audit: test the needle at 10 evenly-spaced positions
    heatmap = lens.audit(
        needle=needle,
        haystack=haystack,
        positions=10,
        verbose=True,
    )

    # Print the full report
    heatmap.report(verbose=True)

    # Access results programmatically
    print("\nProgrammatic access:")
    print(f"  retrieval_score = {heatmap.retrieval_score:.1%}")
    print(f"  verdict         = {heatmap.verdict}")
    print(f"  fault_zones     = {heatmap.fault_zones}")
    print(f"  fault_label     = {heatmap.fault_zone_label}")

    # CI gate check
    passed, message = lens.ci_gate([heatmap], min_score=0.80)
    print(f"\nCI Gate: {message}")
    print(f"Exit code would be: {'0 (PASS)' if passed else '1 (FAIL)'}")

    return heatmap


if __name__ == "__main__":
    mock = "--mock" in sys.argv
    run_example(mock=mock)
