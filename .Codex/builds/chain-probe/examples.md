# chain-probe — Usage Examples

---

## Example 1: Basic RAG Pipeline Probe

```python
"""
Basic usage: Instrument a 3-step RAG pipeline and locate the fault.
"""
from chain_probe import probe, ProbeSession, FaultLocator

# --- Step 1: Retrieval ---
@probe(
    name="retrieve",
    expected_keywords=["document", "relevant", "result"],
    tags={"step": "retrieval", "model": "text-embedding-3-small"}
)
def retrieve(query: str, top_k: int = 5) -> list[str]:
    # Your vector DB search here
    results = vector_db.similarity_search(query, k=top_k)
    return [r.page_content for r in results]


# --- Step 2: Re-ranking ---
@probe(
    name="rerank",
    expected_keywords=["score", "ranked"],
    tags={"step": "reranking", "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"}
)
def rerank(docs: list[str], query: str) -> list[str]:
    # Your re-ranking logic here
    return reranker.rerank(docs, query)


# --- Step 3: LLM Synthesis ---
@probe(
    name="synthesize",
    expected_keywords=["answer", "based on", "according to"],
    forbidden_keywords=["I don't know", "I cannot", "no information"],
    tags={"step": "synthesis", "model": "gpt-4o"}
)
def synthesize(context: list[str], query: str) -> str:
    prompt = f"Context: {chr(10).join(context)}\n\nQuestion: {query}\n\nAnswer:"
    return llm.complete(prompt)


# --- Run with ProbeSession ---
with ProbeSession(name="rag_run_001") as session:
    docs = retrieve("What are the main causes of inflation?")
    ranked = rerank(docs, "What are the main causes of inflation?")
    answer = synthesize(ranked, "What are the main causes of inflation?")

print(f"Answer: {answer}")

# --- Locate the fault ---
report = FaultLocator(session).locate()
print(report.summary())

# Example output:
# Step [retrieve]    fault_score=0.83  ORIGIN ← ORIGIN FAULT
# Step [rerank]      fault_score=0.61  CASCADE (cascade)
# Step [synthesize]  fault_score=0.09  PASS
#
# FAULT LOCATED: retrieve (confidence: HIGH)
# RECOMMENDATION: Step 'retrieve' produced output with low semantic score.
#                 Missing expected keywords: ['document', 'relevant'].
#                 Use 'probe replay' to test this step in isolation.
```

---

## Example 2: Step Replay for Debugging

```python
"""
After locating the fault in retrieval, replay with different parameters.
"""
from chain_probe import ProbeSession, StepReplay

# Load the past session
session = ProbeSession.load("your-session-id-here")

replay = StepReplay(session, step_name="retrieve")

# Three Elijah water pours: three deliberate parameter variations
result_1 = replay.run(func=retrieve, top_k=10)         # More documents
result_2 = replay.run(func=retrieve, top_k=5, threshold=0.7)  # Higher similarity threshold
result_3 = replay.run(func=retrieve_v2, top_k=5)       # Different retrieval function

# Compare all runs
comparison = replay.compare([result_1, result_2, result_3])
print(f"Best parameters: {comparison['best_params']}")
print(f"Best score: {comparison['best_score']:.3f}")

# Example output:
# Best parameters: {'func': retrieve_v2, 'top_k': 5}
# Best score: 0.871
# Verdict: FAULT_MITIGATED
```

---

## Example 3: CI/CD Integration

```python
"""
pytest integration for automated pipeline quality gates.
"""
import pytest
from chain_probe import probe, ProbeSession, FaultLocator


@probe(name="retrieve", expected_keywords=["result", "document"])
def retrieve(query: str) -> list[str]:
    return pipeline.retrieve(query)


@probe(name="answer", expected_keywords=["answer", "based"])
def answer(context: list[str], query: str) -> str:
    return pipeline.answer(context, query)


def test_rag_pipeline_quality():
    """All pipeline steps must pass fault detection."""
    with ProbeSession(name=f"ci_test_{pytest.current_test_id}") as session:
        docs = retrieve("What is retrieval-augmented generation?")
        result = answer(docs, "What is retrieval-augmented generation?")

    report = FaultLocator(session, fault_threshold=0.5).locate()

    assert report.fault_step is None, (
        f"Pipeline fault detected at step '{report.fault_step}' "
        f"(score={report.fault_score:.2f}, confidence={report.fault_confidence}).\n"
        f"Cascade steps: {report.cascade_steps}\n"
        f"Recommendation: {report.recommendation}\n"
        f"\n{report.summary()}"
    )


def test_retrieval_step_quality():
    """Retrieval step must maintain semantic quality independently."""
    with ProbeSession(name="ci_retrieval_only") as session:
        docs = retrieve("test query for quality check")

    report = FaultLocator(session, fault_threshold=0.4).locate()
    assert report.fault_step is None, f"Retrieval quality below threshold: {report.summary()}"
```

---

## Example 4: Multi-Step Agent Pipeline

```python
"""
Instrument a multi-step LLM agent: planner → tool_selector → executor → validator.
"""
from chain_probe import probe, ProbeSession, FaultLocator, StepReplay

@probe(
    name="planner",
    expected_keywords=["step", "plan", "action"],
    tags={"agent_type": "planner"}
)
def plan(goal: str) -> dict:
    """Generate a step-by-step plan for the agent."""
    response = llm.complete(f"Create a step-by-step plan to: {goal}")
    return parse_plan(response)


@probe(
    name="tool_selector",
    expected_keywords=["tool", "function", "call"],
    forbidden_keywords=["error", "invalid"],
    tags={"agent_type": "tool_selector"}
)
def select_tool(plan_step: str) -> str:
    """Select the right tool for a given plan step."""
    return llm.complete(f"Which tool should I use for: {plan_step}? Available: {AVAILABLE_TOOLS}")


@probe(
    name="executor",
    expected_keywords=["result", "output", "completed"],
    tags={"agent_type": "executor"}
)
def execute(tool_name: str, plan_step: str) -> str:
    """Execute the selected tool."""
    return tools[tool_name].run(plan_step)


@probe(
    name="validator",
    expected_keywords=["valid", "correct", "verified"],
    forbidden_keywords=["incorrect", "wrong", "failed"],
    tags={"agent_type": "validator"}
)
def validate(execution_result: str, original_goal: str) -> str:
    """Validate that the execution result satisfies the original goal."""
    return llm.complete(
        f"Does this result satisfy the goal '{original_goal}'?\nResult: {execution_result}\n"
        "Respond with 'valid: [yes/no] because [reason]'"
    )


# Run the agent
goal = "Find the latest AI papers published this week and summarize the top 3"
with ProbeSession(name="agent_run_001") as session:
    plan_result = plan(goal)
    tool = select_tool(plan_result["first_step"])
    result = execute(tool, plan_result["first_step"])
    validation = validate(result, goal)

# Fault report
report = FaultLocator(session).locate()
print(report.summary())

# Generate coverage map
from chain_probe.probe_map import ProbeMap
ProbeMap(session).generate("agent_coverage.html")
```

---

## Example 5: CLI Workflow

```bash
# Run your pipeline script with probe instrumentation
probe run python my_rag_pipeline.py --session prod_run_2026_03_27

# Check fault report
probe report --session prod_run_2026_03_27
# Output:
# ┌─────────────────────────────────────────────────────────┐
# │ chain-probe FaultReport — Session: prod_run_2026_03_27  │
# ├──────────┬─────────────┬────────────┬───────────────────┤
# │ Step     │ fault_score │ fault_type │ duration_ms       │
# ├──────────┼─────────────┼────────────┼───────────────────┤
# │ retrieve │   0.83      │ ORIGIN     │ 124.3             │
# │ rerank   │   0.61      │ CASCADE    │ 88.1              │
# │ synthesize│  0.09      │ PASS       │ 1204.7            │
# └──────────┴─────────────┴────────────┴───────────────────┘
# FAULT: retrieve (confidence: HIGH)

# Replay the failing step
probe replay --session prod_run_2026_03_27 --step retrieve \
  --func my_pipeline.retrieve --param top_k=10

# Generate visual coverage map
probe map --session prod_run_2026_03_27 --output coverage.html

# Use in CI (exits non-zero if fault detected)
probe ci --session prod_run_2026_03_27 --threshold 0.5
echo "Exit code: $?"  # 0 = pass, 1 = fault detected
```

---

## Example 6: LLM Judge Integration

```python
"""
Add an LLM judge (optional Level 3) for more accurate fault scoring.
"""
import anthropic
from chain_probe import probe, ProbeSession, FaultLocator

client = anthropic.Anthropic()

def anthropic_judge(step_name: str, inputs: dict, output: str, expected: str) -> float:
    """LLM judge using Claude Haiku for speed and cost efficiency."""
    query = inputs.get("kwargs", {}).get("query", inputs.get("args", [""])[0] if inputs.get("args") else "")

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=5,
        messages=[{
            "role": "user",
            "content": (
                f"Rate this step output from 0-10 (10=perfect, 0=completely wrong).\n"
                f"Step: {step_name}\n"
                f"Query/Input: {query}\n"
                f"Output: {output[:500]}\n\n"
                f"Respond with ONLY a number 0-10."
            )
        }]
    )

    try:
        return float(response.content[0].text.strip()) / 10.0
    except (ValueError, IndexError):
        return 0.5  # Neutral on parse failure


@probe(name="retrieve", expected_keywords=["document"])
def retrieve(query: str) -> list[str]:
    return vector_db.search(query)

@probe(name="synthesize")
def synthesize(docs: list[str], query: str) -> str:
    return llm.complete(f"Context: {docs}\n\nAnswer: {query}")


with ProbeSession(name="llm_judge_run") as session:
    docs = retrieve("Explain quantum entanglement simply")
    answer = synthesize(docs, "Explain quantum entanglement simply")

# Fault report WITH LLM judge
report = FaultLocator(session, llm_judge=anthropic_judge).locate()
print(report.summary())
```
