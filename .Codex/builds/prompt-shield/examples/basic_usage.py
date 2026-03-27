"""
prompt-shield — Basic Usage Example

Demonstrates:
1. BrittlenessRunner with a simple LLM function
2. Reading the BrittleCertificate
3. Fault line analysis

Biblical Foundation:
- PAT-048 (Daniel 5:25-28): TEKEL audit — weighed and found wanting
- PAT-049 (Matthew 7:24-27): Two Builders — storm reveals foundation quality
- PAT-050 (Proverbs 17:3): Crucible — stress test produces certificate of quality
"""

from prompt_shield import BrittlenessEngine, BrittlenessRunner, FaultLineAnalyzer
import anthropic


def customer_service_handler(user_input: str) -> str:
    """
    Example LLM function: a customer service assistant.
    This prompt is being audited for brittleness across paraphrase variants.
    """
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=512,
        system=(
            "You are a helpful customer service assistant for a digital bank. "
            "Answer questions about account balances, transactions, and account management. "
            "Be concise and specific. Always confirm the account type when mentioning balances."
        ),
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text


def run_basic_check():
    """Run a basic brittleness check on the customer service handler."""

    # Configure the engine
    # Matthew 7 — Three storm vectors: lexical (rain), semantic (wind)
    engine = BrittlenessEngine(
        variants_per_input=8,
        levels=["lexical", "semantic"],
        min_similarity=0.75   # Reject low-quality paraphrases
    )

    runner = BrittlenessRunner(
        llm_function=customer_service_handler,
        engine=engine,
        store_path="./shield_demo.db"
    )

    # Test inputs — what the customer service handler will be tested on
    test_inputs = [
        "What is my checking account balance?",
        "How do I transfer money to another account?",
        "I need to dispute a charge on my statement."
    ]

    print("=" * 60)
    print("prompt-shield — BrittlenessAudit")
    print("The TEKEL test: weighing the prompt on the scales")
    print("=" * 60)

    result = runner.run(
        test_inputs=test_inputs,
        threshold=0.30,
        prompt_name="customer_service_v1"
    )

    # Print the verdict
    print(f"\nBrittlenessScore: {result.score:.4f}")
    print(f"Verdict:          {result.verdict}")
    print(f"Variants tested:  {result.certificate.variant_count}")
    print(f"Duration:         {result.run_duration_seconds:.1f}s")
    print(f"Certificate ID:   {result.certificate.certificate_id}")

    # Level breakdown
    print("\nLevel Breakdown:")
    for lb in result.certificate.level_breakdown:
        verdict_symbol = {"ROBUST": "✅", "CONDITIONAL": "⚠️", "BRITTLE": "❌"}[lb.verdict]
        print(f"  {lb.level:12} {lb.score:.4f}  {lb.deviant_count}/{lb.variant_count} deviant  {verdict_symbol} {lb.verdict}")

    # Fault lines (if any)
    if result.certificate.fault_lines:
        print("\nFault Lines Detected:")
        for i, fl in enumerate(result.certificate.fault_lines[:3], 1):
            print(f"\n  {i}. [{fl.level}] '{fl.variant}'")
            print(f"     Deviation: {fl.deviation_score:.4f}")
            print(f"     Fix: {fl.recommendation}")
    else:
        print("\nNo fault lines detected. Prompt is semantically robust.")

    # Save certificate
    cert_json = result.certificate.to_json()
    with open("./shield_certificate_demo.json", "w") as f:
        f.write(cert_json)
    print(f"\nCertificate written to: ./shield_certificate_demo.json")

    # Markdown report
    cert_md = result.certificate.to_markdown()
    with open("./shield_report_demo.md", "w") as f:
        f.write(cert_md)
    print(f"Report written to: ./shield_report_demo.md")

    return result


def run_decorator_example():
    """
    Demonstrates the @brittle_check decorator.
    In test mode (SHIELD_CHECK=true), the decorator runs a brittleness audit
    before the function executes.
    """
    import os
    os.environ["SHIELD_CHECK"] = "true"

    from prompt_shield import brittle_check

    @brittle_check(
        threshold=0.25,
        variants=6,
        levels=["lexical", "semantic"],
        test_inputs=["What is my balance?", "Show me my account info"]
    )
    def account_query_handler(user_input: str) -> str:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            system="Answer questions about account balances. Be concise.",
            messages=[{"role": "user", "content": user_input}]
        )
        return response.content[0].text

    print("\n" + "=" * 60)
    print("Decorator Example — @brittle_check")
    print("=" * 60)

    try:
        result = account_query_handler("What is my balance?")
        print("Function returned successfully.")

        if hasattr(account_query_handler, "_last_shield_result"):
            shield_result = account_query_handler._last_shield_result
            print(f"Shield verdict: {shield_result.verdict}")
            print(f"Shield score: {shield_result.score:.4f}")

    except Exception as e:
        if "BrittlePromptError" in type(e).__name__:
            print(f"BRITTLE PROMPT DETECTED: {e}")
            print("Fix the prompt before deploying.")
        else:
            print(f"Error: {e}")

    finally:
        del os.environ["SHIELD_CHECK"]


if __name__ == "__main__":
    print("Running basic brittleness check...")
    print("(Requires ANTHROPIC_API_KEY environment variable)\n")
    result = run_basic_check()

    print("\n\nRunning decorator example...")
    run_decorator_example()
