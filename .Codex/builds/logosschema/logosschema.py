"""
LogosSchema — Schema-First Business Design Tool
Source Pattern: PAT-012 (John 1:1-14 — Logos as constitutional ordering principle)
Build ID: BUILD-002
BibleWorld Cycle: 001

The Principle:
In the beginning was the Logos — the ordering principle — and it preceded creation.
"Let there be light" works because the Logos already defined what light is.
In business: the schema (information architecture) must precede the code.
LogosSchema extracts the Logos (schema) from a founder's business description.

Architecture:
  Business description (natural language) →
  Entity extraction →
  Relationship mapping →
  Rule inference →
  ER diagram (Mermaid) + API sketch + governance doc

This file is the week-1 prototype: a CLI tool that uses Claude (via API)
to extract a business schema from natural language and outputs:
  1. A Mermaid ER diagram (paste into mermaid.live to visualize)
  2. A list of core API endpoints
  3. Key governance rules inferred from the business description

Usage:
    python logosschema.py
    (prompts for business description interactively)

    OR:
    python logosschema.py --description "I run a cassava flour processing business..."
"""

import argparse
import sys
import textwrap
import os


# ---------------------------------------------------------------------------
# Schema data classes
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field


@dataclass
class Entity:
    name: str
    attributes: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    label: str           # e.g. "places", "belongs_to", "produces"
    cardinality: str     # e.g. "1:N", "N:M", "1:1"


@dataclass
class GovernanceRule:
    rule: str
    entity: str          # which entity this rule applies to
    enforcement: str     # "required" / "recommended" / "warning"


@dataclass
class BusinessSchema:
    business_name: str
    business_type: str
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    rules: list[GovernanceRule] = field(default_factory=list)
    api_endpoints: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema extractor (Claude-backed in production; rule-based stub for offline)
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are a senior software architect helping a founder define the information architecture of their business BEFORE writing any code.

The founder has described their business below. Your job is to extract:
1. ENTITIES — the core objects the business manages (customers, orders, products, employees, transactions, etc.)
2. RELATIONSHIPS — how entities relate to each other (a customer PLACES many orders; a product BELONGS TO a category)
3. RULES — business logic that must be enforced in the data model (every order must have a customer; payment must be received before fulfilment; inventory cannot go below zero)
4. API ENDPOINTS — the 5-8 most critical API endpoints this business needs (in REST format)

BUSINESS DESCRIPTION:
{description}

RESPOND IN THIS EXACT FORMAT (do not deviate — this is parsed programmatically):

ENTITIES:
- EntityName: attribute1, attribute2, attribute3 | Notes: any notes

RELATIONSHIPS:
- EntityA VERB EntityB [cardinality: 1:N] | Label: description

RULES:
- REQUIRED: rule description [entity: EntityName]
- RECOMMENDED: rule description [entity: EntityName]

API_ENDPOINTS:
- GET /resource — description
- POST /resource — description

Keep it focused. 5-10 entities max. 5-15 relationships. 5-10 rules. 5-8 endpoints.
The founder will use this to brief a developer or build the schema themselves."""


def extract_schema_with_claude(description: str, api_key: str) -> str:
    """
    Calls Claude API to extract schema from business description.
    Returns raw text response for parsing.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(description=description)
            }]
        )
        return message.content[0].text
    except ImportError:
        return _offline_stub(description)
    except Exception as e:
        print(f"[Claude API error: {e}] Falling back to offline stub.", file=sys.stderr)
        return _offline_stub(description)


def _offline_stub(description: str) -> str:
    """
    Offline fallback: returns a generic schema template.
    Replace this with real Claude API calls when API key is available.
    """
    return textwrap.dedent("""
    ENTITIES:
    - Customer: id, name, phone, email, location | Notes: Primary revenue source
    - Product: id, name, category, unit_price, stock_quantity | Notes: Track stock carefully
    - Order: id, customer_id, created_at, status, total_amount | Notes: Status: pending/confirmed/delivered/cancelled
    - Payment: id, order_id, amount, method, paid_at | Notes: method: mobile_money/cash/bank_transfer
    - Supplier: id, name, phone, location, reliability_score | Notes: Rate suppliers to avoid FP-005

    RELATIONSHIPS:
    - Customer PLACES Order [cardinality: 1:N] | Label: one customer can place many orders
    - Order CONTAINS Product [cardinality: N:M] | Label: orders contain multiple products
    - Order HAS_ONE Payment [cardinality: 1:1] | Label: each order has one payment record
    - Supplier DELIVERS Product [cardinality: N:M] | Label: suppliers provide multiple products

    RULES:
    - REQUIRED: Every Order must have a valid Customer ID [entity: Order]
    - REQUIRED: Payment.amount must equal Order.total_amount before status='delivered' [entity: Payment]
    - REQUIRED: Product.stock_quantity cannot go below 0 [entity: Product]
    - RECOMMENDED: Customer.phone must be unique — prevents duplicate accounts [entity: Customer]
    - RECOMMENDED: Supplier.reliability_score updated after each delivery [entity: Supplier]

    API_ENDPOINTS:
    - POST /customers — create new customer
    - GET /customers/{id} — get customer details
    - POST /orders — create new order
    - GET /orders/{id} — get order with line items
    - POST /orders/{id}/payment — record payment for order
    - GET /products — list all products with stock
    - PUT /products/{id}/stock — update stock after delivery
    - GET /reports/revenue?from=&to= — revenue report for date range
    """)


# ---------------------------------------------------------------------------
# Schema parser
# ---------------------------------------------------------------------------

def parse_schema_response(raw: str, business_name: str = "Business") -> BusinessSchema:
    schema = BusinessSchema(business_name=business_name, business_type="General")
    current_section = None

    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("ENTITIES:"):
            current_section = "entities"
        elif line.startswith("RELATIONSHIPS:"):
            current_section = "relationships"
        elif line.startswith("RULES:"):
            current_section = "rules"
        elif line.startswith("API_ENDPOINTS:"):
            current_section = "endpoints"
        elif line.startswith("- ") and current_section:
            content = line[2:]

            if current_section == "entities":
                parts = content.split("|")
                name_attrs = parts[0].split(":")
                name = name_attrs[0].strip()
                attrs = [a.strip() for a in name_attrs[1].split(",")] if len(name_attrs) > 1 else []
                notes = parts[1].replace("Notes:", "").strip() if len(parts) > 1 else ""
                schema.entities.append(Entity(name=name, attributes=attrs, notes=notes))

            elif current_section == "relationships":
                parts = content.split("|")
                rel_part = parts[0].strip()
                label = parts[1].replace("Label:", "").strip() if len(parts) > 1 else rel_part
                words = rel_part.split()
                if len(words) >= 3:
                    from_entity = words[0]
                    verb = words[1]
                    to_entity = words[2]
                    cardinality = "1:N"
                    if "[cardinality:" in rel_part:
                        c_start = rel_part.index("[cardinality:") + 13
                        c_end = rel_part.index("]", c_start)
                        cardinality = rel_part[c_start:c_end].strip()
                    schema.relationships.append(Relationship(
                        from_entity=from_entity,
                        to_entity=to_entity,
                        label=f"{verb} ({label})",
                        cardinality=cardinality
                    ))

            elif current_section == "rules":
                enforcement = "recommended"
                rule_text = content
                if content.startswith("REQUIRED:"):
                    enforcement = "required"
                    rule_text = content[9:].strip()
                elif content.startswith("RECOMMENDED:"):
                    enforcement = "recommended"
                    rule_text = content[12:].strip()

                entity = "General"
                if "[entity:" in rule_text:
                    e_start = rule_text.index("[entity:") + 8
                    e_end = rule_text.index("]", e_start)
                    entity = rule_text[e_start:e_end].strip()
                    rule_text = rule_text[:rule_text.index("[entity:")].strip()

                schema.rules.append(GovernanceRule(rule=rule_text, entity=entity, enforcement=enforcement))

            elif current_section == "endpoints":
                schema.api_endpoints.append(content)

    return schema


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def to_mermaid_er(schema: BusinessSchema) -> str:
    lines = ["erDiagram"]
    for entity in schema.entities:
        lines.append(f"    {entity.name} {{")
        for attr in entity.attributes[:6]:  # Mermaid handles limited attrs cleanly
            safe_attr = attr.replace(" ", "_").replace("-", "_")
            lines.append(f"        string {safe_attr}")
        lines.append("    }")

    for rel in schema.relationships:
        # Mermaid ER cardinality notation
        card_map = {
            "1:N": "||--o{",
            "N:M": "}o--o{",
            "1:1": "||--||",
        }
        crow = card_map.get(rel.cardinality, "||--o{")
        label = rel.label[:30].replace('"', "'")
        lines.append(f'    {rel.from_entity} {crow} {rel.to_entity} : "{label}"')

    return "\n".join(lines)


def to_governance_doc(schema: BusinessSchema) -> str:
    lines = [
        f"# {schema.business_name} — Data Governance Rules",
        "",
        "These rules MUST be enforced at the application and database level.",
        "Required rules = data integrity constraints. Recommended = application-layer validation.",
        "",
    ]
    required = [r for r in schema.rules if r.enforcement == "required"]
    recommended = [r for r in schema.rules if r.enforcement != "required"]

    if required:
        lines.append("## REQUIRED (Data Integrity)")
        for r in required:
            lines.append(f"- [{r.entity}] {r.rule}")
        lines.append("")

    if recommended:
        lines.append("## RECOMMENDED (Application Logic)")
        for r in recommended:
            lines.append(f"- [{r.entity}] {r.rule}")

    return "\n".join(lines)


def print_full_output(schema: BusinessSchema):
    print("\n" + "=" * 60)
    print(f"LOGOSSCHEMA OUTPUT — {schema.business_name}")
    print("=" * 60)

    print("\n--- MERMAID ER DIAGRAM ---")
    print("(paste at https://mermaid.live to visualize)\n")
    print(to_mermaid_er(schema))

    print("\n--- API ENDPOINTS ---")
    for ep in schema.api_endpoints:
        print(f"  {ep}")

    print("\n--- GOVERNANCE RULES ---")
    print(to_governance_doc(schema))

    print("\n--- NEXT STEPS ---")
    print("1. Review entities — are any missing? Any unnecessary?")
    print("2. Paste the Mermaid diagram into mermaid.live and share with your developer")
    print("3. Add the governance rules as database constraints and application validations")
    print("4. Use the API endpoints as your first sprint backlog")
    print("5. Do NOT write code until this schema is reviewed and approved")
    print()


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LogosSchema — Schema-first business design. Define your Logos before you build."
    )
    parser.add_argument(
        "--description", "-d",
        type=str,
        help="Business description (or omit to enter interactively)",
        default=None
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        help="Business name",
        default="My Business"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
        default=os.environ.get("ANTHROPIC_API_KEY", "")
    )
    args = parser.parse_args()

    description = args.description
    if not description:
        print("LogosSchema — Schema-First Business Design")
        print("------------------------------------------")
        print("In the beginning was the Logos. Define your schema before you build.\n")
        print("Describe your business in plain English (2-5 sentences).")
        print("What does it do? Who does it serve? What does it track?\n")
        description = input("> ").strip()
        if not description:
            print("No description provided. Exiting.")
            sys.exit(1)

    print("\nExtracting schema from your business description...")
    raw = extract_schema_with_claude(description, args.api_key)
    schema = parse_schema_response(raw, business_name=args.name)
    print_full_output(schema)


if __name__ == "__main__":
    main()
