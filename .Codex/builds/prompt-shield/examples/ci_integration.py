"""
prompt-shield — CI Integration Example

Demonstrates:
1. shield.yaml configuration loading
2. CI gate (exit code 0/1)
3. GitHub Actions workflow integration
4. BaselineRegistry usage

Biblical Foundation:
- PAT-048 (Daniel 5:25-28): "TEKEL — weighed on the scales and found wanting"
  The CI gate IS the scales. Exit code 1 = found wanting. Deployment blocked.
"""

# Example shield.yaml configuration
SHIELD_YAML_EXAMPLE = """
# shield.yaml — prompt-shield configuration

prompts:
  - name: customer_service_assistant
    function: myapp.prompts.customer_service_handler
    test_inputs:
      - "What is my account balance?"
      - "How do I transfer money?"
      - "I need to dispute a charge"
    threshold: 0.25
    levels: [lexical, semantic]
    variants_per_input: 8

  - name: document_summarizer
    function: myapp.prompts.summarize_document
    test_inputs:
      - "Summarize this financial report."
      - "What are the key points in this document?"
    threshold: 0.30
    levels: [lexical, syntactic, semantic]
    variants_per_input: 10

output:
  certificate: shield-certificate.json
  report: shield-report.md
  store: ./shield.db
"""

# GitHub Actions workflow YAML
GITHUB_ACTIONS_WORKFLOW = """
# .github/workflows/prompt-shield.yml
name: Prompt Brittleness Check

on:
  push:
    branches: [main, develop]
    paths:
      - 'prompts/**'
      - 'myapp/prompts/**'
  pull_request:
    paths:
      - 'prompts/**'
      - 'myapp/prompts/**'

jobs:
  shield:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install prompt-shield
        run: |
          pip install prompt-shield[t5]
          # Or with LLM-generated paraphrases:
          # pip install prompt-shield[llm]

      - name: Run brittleness audit
        run: shield ci --config shield.yaml --threshold 0.30
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload BrittleCertificate
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: brittle-certificate-${{ github.sha }}
          path: |
            shield-certificate.json
            shield-report.md
          retention-days: 90

      - name: Comment on PR
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const cert = JSON.parse(fs.readFileSync('shield-certificate.json', 'utf8'));
            const body = `## Prompt Brittleness Check Failed

            **BrittlenessScore:** ${cert.brittleness_score.toFixed(4)} > threshold ${cert.threshold}
            **Verdict:** ${cert.verdict}
            **Certificate ID:** \`${cert.certificate_id}\`

            ### Fault Lines
            ${cert.fault_lines.slice(0, 3).map(f =>
              `- **[${f.level}]** \`${f.variant}\` (deviation: ${f.deviation_score.toFixed(4)})`
            ).join('\\n')}

            **Fix:** ${cert.fault_lines[0]?.recommendation || 'Review prompt for surface-form dependency.'}
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
"""

# Baseline Registry example
BASELINE_EXAMPLE = """
from prompt_shield import BrittlenessRunner, BrittlenessEngine, BaselineRegistry
import anthropic

def my_prompt(user_input: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=512,
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text

# First time: run audit and register baseline
engine = BrittlenessEngine(variants_per_input=10, levels=["lexical", "semantic"])
runner = BrittlenessRunner(llm_function=my_prompt, engine=engine)
result = runner.run(
    test_inputs=["What is my balance?"],
    threshold=0.30,
    prompt_name="my_prompt_v1"
)

registry = BaselineRegistry(store_path="./shield.db")

if result.verdict in ["ROBUST", "CONDITIONAL"]:
    registry.register(
        prompt_name="my_prompt_v1",
        score=result.score,
        verdict=result.verdict,
        certificate_id=result.certificate.certificate_id
    )
    print(f"Baseline registered: {result.score:.4f} ({result.verdict})")

# Later (after prompt changes): check for regression
result_v2 = runner.run(
    test_inputs=["What is my balance?"],
    threshold=0.30,
    prompt_name="my_prompt_v1"
)

regression = registry.check_regression(
    prompt_name="my_prompt_v1",
    current_score=result_v2.score,
    max_regression=0.05  # Alert if brittleness worsened by > 5%
)

if regression.detected:
    print(f"BRITTLENESS REGRESSION DETECTED!")
    print(f"Previous score: {regression.previous:.4f}")
    print(f"Current score: {regression.current:.4f}")
    print(f"Worsening: {regression.delta:+.4f}")
else:
    print(f"No regression. Current score {result_v2.score:.4f} within tolerance.")
"""

if __name__ == "__main__":
    print("prompt-shield CI Integration Examples")
    print("=" * 60)

    print("\n1. shield.yaml configuration:")
    print(SHIELD_YAML_EXAMPLE)

    print("\n2. GitHub Actions workflow:")
    print(GITHUB_ACTIONS_WORKFLOW)

    print("\n3. Baseline Registry usage:")
    print(BASELINE_EXAMPLE)
