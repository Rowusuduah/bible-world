# BibleWorld Cycle 011 — Build Specifications

**Cycle:** 011
**Date:** 2026-03-27
**New Builds This Cycle:** 1 (BUILD-010: drift-guard)
**Build Score:** 9.3
**Pivot_Score:** 8.60

---

## BUILD-010: drift-guard

### Overview
**Name:** drift-guard
**Tagline:** Verify that pull requests do what they say.
**Pattern Source:** PAT-036 (Romans 7:7 — The Law Makes Violations Visible)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Pivot_Score:** 8.60 (new record holder joint second-place with no other tool in BibleWorld history above this except prompt-lock at 8.70)

### Problem Statement

AI generates 42% of all code in 2026. AI-assisted pull requests create 1.7x more production issues than human PRs. The root cause is intent drift: the PR description says "fix null pointer in user registration" and the AI code broadly does that — but also silently removes an adjacent auth check. Tests pass. Code review misses it. Production breaks.

No open-source tool exists that systematically verifies whether a PR's code changes actually fulfill the stated intent. Code review tools (CodeRabbit, PR-Agent) review quality and style. Linters review syntax. CI pipelines run tests. Nobody checks the semantic gap between PR description and diff.

Salesforce has an internal system ("intent reconstruction") addressing this. No open-source version exists. This is the gap.

### Who It Serves

**Primary persona:** AI/ML engineers and senior developers at companies using AI-assisted coding (Copilot, Cursor, Claude, etc.) who are experiencing elevated production incidents from AI-generated code.

**Secondary personas:**
- Platform engineers standardizing code review practices for AI-accelerated teams
- Engineering managers who want audit trails for PR intent verification
- Open-source project maintainers receiving AI-generated contributions they cannot fully review

**Scale of audience:** Every team using GitHub/GitLab with AI coding tools. This is essentially all of Big Tech and most startups in 2026.

### How It Works — Detailed Technical Specification

#### Layer 1: Intent Parser
```
Input:  PR title (string) + PR description (string)
Output: List[IntentClause]
        - text: str (original clause text)
        - clause_type: str ("adds" | "removes" | "modifies" | "fixes" | "ensures" | "does_not")
        - subject: str (noun phrase extracted from clause)
        - confidence: float (1.0 default from regex; will be LLM-assigned in v0.2)
```

Method: Regex pattern matching on English verb clusters (adds/creates/introduces, removes/deletes, updates/modifies, fixes/resolves, ensures/validates, does not/should not/won't).

Sentence boundaries: split on `.!?\n` and bullet point markers `[-*•]`.

Capped at 12 clauses to manage LLM token cost (average PR has 3-8 meaningful clauses).

#### Layer 2: Diff Fetcher + Parser
```
Input:  base git ref (default: HEAD~1), head git ref (default: HEAD)
        OR pre-computed diff text
Output: List[DiffHunk]
        - file_path: str
        - old_start: int
        - new_start: int
        - lines_added: List[str]
        - lines_removed: List[str]
```

Method: `git diff base..head --unified=5` via subprocess. Parse unified diff format.
Truncation: diff text truncated to 8000 characters before sending to LLM (handles 90% of PRs).
Large PR handling (v0.2): pre-summarize changed functions with `git diff --stat` + function-level parsing before passing to LLM.

#### Layer 3: LLM Verifier (Claude)
```
Input:  List[IntentClause] + diff text + PR title + PR description
Output: Dict with:
        - clauses: List[{clause_index, status, confidence, evidence, explanation}]
        - overall_status: "PASS" | "FAIL" | "WARN"
        - overall_confidence: float 0.0-1.0
        - drift_score: float 0.0-1.0
        - intent_summary: str (2-3 sentence synthesis)
```

Model: claude-3-5-haiku-20241022 (default, fast, cheap)
High-stakes option: claude-3-5-sonnet-20241022 (set via DRIFT_GUARD_MODEL)
Average tokens per verification: ~3,000 input + ~600 output ≈ $0.002-0.005 per PR

System prompt design: Structured judge prompt with explicit JSON schema. Instructs Claude to:
1. Find evidence quotes from the diff for each clause
2. Classify each clause PASS/FAIL/WARN/SKIP
3. Be conservative — if the diff doesn't show it, say so
4. Flag scope creep (diff exceeds stated intent)
5. Pay attention to "does not" clauses — silent changes violate these hardest

#### Layer 4: SQLite Trace Log
```
Schema:
  id INTEGER PRIMARY KEY AUTOINCREMENT
  timestamp TEXT
  commit_sha TEXT
  pr_title TEXT
  overall_status TEXT
  drift_score REAL
  overall_confidence REAL
  files_changed TEXT (JSON array)
  lines_added INTEGER
  lines_removed INTEGER
  report_json TEXT (full DriftReport as JSON)
```

Default path: `.drift-guard.db` in repo root.
Override: `DRIFT_GUARD_DB` environment variable.

History command: `drift-guard history --n 20` shows recent verifications with drift scores.
V0.2: Team dashboard aggregating drift scores across all PRs over time.

### Drift Score Formula

Drift score is computed by the LLM, not by a formula, but the guidelines given to the LLM:

- **0.00**: Every clause PASS. Diff exactly matches stated intent.
- **0.10–0.29**: Minor gaps or ambiguities. One clause WARN. Overall WARN.
- **0.30–0.59**: Meaningful gap. At least one FAIL clause, or multiple WARNs.
- **0.60–0.79**: Significant drift. Multiple FAILs. Code does less or different than stated.
- **0.80–1.00**: Complete mismatch. PR says one thing; code does another.

Default CI threshold: **0.30**. Above this, CI gate fails.
Configurable via `--threshold` flag or `.drift-guard.toml`.

### Cost Analysis

| Component | Cost per PR |
|-----------|------------|
| Claude 3.5 Haiku (input ~3000 tokens) | $0.0009 |
| Claude 3.5 Haiku (output ~600 tokens) | $0.0018 |
| **Total per PR** | **~$0.003** |
| 100 PRs/month | $0.30 |
| 1000 PRs/month (large team) | $3.00 |
| 10,000 PRs/month (Big Tech team) | $30.00 |

This is cheaper than one minute of a senior engineer's time. The value proposition is clear.

### GitHub Action (Full Specification)

```yaml
# .github/workflows/drift-guard.yml
name: drift-guard — PR Intent Verification

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  drift-guard:
    name: Verify PR intent
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write    # To post comment with report
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0      # Full history for accurate diffs

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install drift-guard
        run: pip install drift-guard

      - name: Run drift-guard verification
        id: drift
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          drift-guard verify \
            --title "${{ github.event.pull_request.title }}" \
            --description "${{ github.event.pull_request.body }}" \
            --base origin/${{ github.base_ref }} \
            --head ${{ github.event.pull_request.head.sha }} \
            --format json > drift-report.json

          # Extract drift score for badge
          DRIFT_SCORE=$(python3 -c "import json; d=json.load(open('drift-report.json')); print(d['drift_score'])")
          echo "drift_score=$DRIFT_SCORE" >> $GITHUB_OUTPUT

          # Fail if score exceeds threshold
          python3 -c "
          import json, sys
          d = json.load(open('drift-report.json'))
          threshold = 0.30
          if d['drift_score'] > threshold:
              print(f'FAIL: drift score {d[\"drift_score\"]:.2f} exceeds threshold {threshold}')
              sys.exit(1)
          else:
              print(f'PASS: drift score {d[\"drift_score\"]:.2f} within threshold {threshold}')
          "

      - name: Generate markdown report
        if: always()
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          drift-guard verify \
            --title "${{ github.event.pull_request.title }}" \
            --description "${{ github.event.pull_request.body }}" \
            --base origin/${{ github.base_ref }} \
            --head ${{ github.event.pull_request.head.sha }} \
            --format markdown \
            --no-save > drift-report.md

      - name: Post drift-guard report as PR comment
        if: always()
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('drift-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### Roadmap

**v0.1 (current — 1-2 week sprint)**
- CLI: `drift-guard verify`, `drift-guard history`
- Python API: `verify()` function
- Claude integration (Haiku default, Sonnet option)
- SQLite trace log
- GitHub Action support
- PyPI: `pip install drift-guard`
- Output: text, JSON, markdown

**v0.2 (3-4 weeks after v0.1)**
- GitLab CI integration
- Automatic PR comment posting (GitHub + GitLab)
- Slack/Teams webhook alerts for high drift scores
- Team drift dashboard (web UI, aggregated metrics)
- Large diff handling (function-level summarization before LLM)
- `.drift-guard.toml` configuration file

**v0.3 (enterprise)**
- Multi-clause dependency analysis
- Custom verification rules per file type (e.g., schema files trigger extra scrutiny)
- Jira/Linear ticket intent integration (pull intent from linked ticket, not just PR body)
- OpenAI/Gemini/Mistral model support
- Production contract monitoring (post-deploy version of pre-merge verification)
- SSO/RBAC for team dashboards

### Why This Will Be Adopted

1. **Zero friction to try:** `pip install drift-guard` + API key. No sign-up, no credit card, no infrastructure.
2. **Immediate value:** First use will catch something. Every AI-assisted team has PRs with intent drift. They will see their first FAIL or WARN immediately.
3. **GitOps native:** Works in any git repo, any CI system. Not locked to GitHub.
4. **Free tier is real:** At $0.003/PR, a team can run 1,000 PRs for $3. No limit imposed by drift-guard itself.
5. **"2026 = year of quality":** The tool is positioned for the exact market shift described by CodeRabbit and Salesforce.
6. **Salesforce validation:** When Salesforce's internal tool becomes public, drift-guard is the open-source answer.
7. **Network effect:** Teams will post drift-guard reports in PRs. Other teams will see them and want the tool.

### Build Score Breakdown

- Feasibility: 3/3 — Pure Python, subprocess, Anthropic API, SQLite. No cloud infrastructure. No custom ML. v0.1 in 1-2 weeks.
- Impact: 2.8/3 — Serves every team using AI-assisted coding (growing from 42% to 80%+). Saves senior engineer time in review.
- Completeness: 2.0/2 — Full spec: CLI, API, architecture, GitHub Action, test suite, pyproject.toml, README.
- Biblical fidelity: 1.5/2 — Romans 7:7 maps structurally and honestly. The law-as-measurement-standard pattern is present in the tool's core function (PR description becomes the law; diff is measured against it).
- **Total: 9.3/10**

### Files Written This Cycle

| File | Lines | Description |
|------|-------|-------------|
| `.Codex/builds/drift-guard/drift_guard.py` | 450+ | Core implementation: all layers, CLI, API |
| `.Codex/builds/drift-guard/README.md` | 300+ | Production-quality OSS README |
| `.Codex/builds/drift-guard/tests/test_drift_guard.py` | 200+ | Test suite with mocked LLM |
| `.Codex/builds/drift-guard/pyproject.toml` | 50 | Package configuration |
