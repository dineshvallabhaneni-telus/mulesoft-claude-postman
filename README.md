# MuleSoft Deployment Validation Framework

A reusable, zero-configuration framework that validates a MuleSoft change set from
GitHub Actions and produces a professional Microsoft Word validation report.

It compares the current source against the **previous deployment's source**, runs the
**full Postman collection**, analyses the risk, and writes a single `.docx` to
`reports/`.

Nothing is cloned. Nothing is downloaded. Anypoint Platform is never contacted.

---

## How it runs

```bash
claude -p "$(cat Prompt/prompt.md)"
```

`Prompt/prompt.md` is the prompt passed to the Claude API. Claude Code executes it
headlessly, running the three phases itself. `.claude/CLAUDE.md` is the standing policy
that applies to every run and is loaded automatically.

---

## Workspace contract

The calling workflow must arrange three things before invoking Claude:

| Path | Contents |
|---|---|
| repository root | current MuleSoft source under validation |
| `previous_ws/` | the previous deployment's MuleSoft source |
| `postman_collection/` | the Postman collection, and its environment file if any |

The framework writes only to `workspace/execution/` and `reports/`.

`.github/workflows/mulesoft-validation.yml` is a working example that populates
`previous_ws/` from a Git ref with `git archive`. Replace that one step if your previous
deployment source comes from somewhere else — the framework only requires that the
directory exists.

---

## Phases

Phase numbering is retained from the previous framework; phases 1 to 3 (environment
validation, fresh clones, Anypoint artifact retrieval) no longer exist.

### Phase 4 — Source Comparison

```bash
python3 scripts/source_compare.py
```

Compares the current source against `previous_ws/` by SHA-256 content hash. Beyond a
line diff it parses the changed files and extracts:

- Mule flow and sub-flow names added or removed
- HTTP listener paths and allowed methods added or removed
- Maven dependencies added, removed, or version-changed
- Property and YAML keys added or removed

Every changed file is classified — `MULE_FLOW`, `API_SPEC`, `DEPENDENCY`, `DATAWEAVE`,
`CONFIGURATION`, `BINARY`, `TEST`, `DOCUMENTATION`, `OTHER` — with an impact level.

Writes `workspace/execution/source-comparison.json`.

Detected changes are the expected input, not a failure. This phase does not gate
phase 5.

### Phase 5 — Postman Testing

```bash
python3 scripts/run_postman.py
```

Runs the **entire** collection from `postman_collection/` with Newman. Every request
executes on every run; the phase 4 diff informs the analysis, never the test selection.

Writes `workspace/execution/postman-results.json` with per-request method, URL,
headers, body, HTTP status, timing, every assertion, and the classified result — all
redacted.

### Phase 6 — Analysis and Report

Claude writes `workspace/execution/analysis.json` — the judgement: high-level changes,
impact narrative, risks, APIs needing attention, and the final recommendation. Then:

```bash
python3 scripts/generate_report.py
```

Renders the `.docx` and re-opens it to verify all required sections exist before
exiting zero.

---

## Report structure

1. Summary — overall result, high-level changes, result counts
2. Source Comparison — changes by category, changed files, behaviour-relevant deltas
3. Postman Test Results — results by folder, failure detail
4. Risk and Impact Analysis — potential issues, APIs requiring attention
5. Final Recommendation — verdict, rationale, concerns, actions

Appendix A complete test case inventory · B per-test execution evidence · C detailed
file change log with diffs · D execution boundaries and compliance.

Sections 1 to 3 and all appendices are generated mechanically from the evidence files.
Sections 4 and 5 come from Claude's `analysis.json`.

---

## Result rules

`PASS` · `FAIL` · `SKIPPED` · `BLOCKED` · `NOT EXECUTED`

A PASS is never inferred. A request that returned 200 but defines no assertions is
`NOT EXECUTED` with the reason recorded — a bare 2xx proves nothing.

The generator reconciles the narrative against the evidence: any failed test forces
`FAIL`, and an unexecuted collection forces `BLOCKED`, regardless of what
`analysis.json` claims.

---

## Configuration

There is no config file and no credentials file. Defaults live in
`scripts/framework_config.py` and any of them can be overridden by an environment
variable of the same name:

```yaml
env:
  TARGET_ENVIRONMENT: QA
  PREVIOUS_WORKSPACE: ./baseline
  NEWMAN_INSECURE: 'true'
```

`APPLICATION_NAME` is derived from the workspace when unset: `pom.xml` `artifactId`,
then the GitHub repository name, then the workspace directory name.

Full list: [.claude/references/configuration.md](.claude/references/configuration.md)

### Secrets

Supply secrets only as environment variables, from GitHub Actions secrets. Everything
the framework writes passes through a redaction filter that masks Bearer and Basic
tokens, credentials embedded in URLs, GitHub PAT-shaped strings, and any value whose
key looks like a password, secret, token, key or credential.

---

## Requirements

| Tool | Purpose |
|---|---|
| Python 3.9+ | the three phase scripts |
| `python-docx` | report generation |
| Newman | Postman collection execution |
| `@anthropic-ai/claude-code` | headless orchestration |

```bash
pip install python-docx
npm install -g newman @anthropic-ai/claude-code
```

---

## Layout

```
Prompt/prompt.md                the prompt passed to the Claude API
.claude/CLAUDE.md               standing policy, auto-loaded
.claude/agents/                 one agent per phase
.claude/skills/                 one skill per phase
.claude/references/             configuration, comparison, execution, report schema
.claude/settings.json           tool permissions and read-only guardrails
scripts/framework_config.py     defaults, path resolution, redaction
scripts/source_compare.py       phase 4
scripts/run_postman.py          phase 5
scripts/generate_report.py      phase 6
.github/workflows/              example calling workflow
```

---

## Boundaries

Read-only: the MuleSoft source, `previous_ws/`, the Postman collection and its
environment file. No Git write operations.

Prohibited: cloning or fetching, downloading deployment artifacts, contacting Anypoint
Platform, deploying or restarting anything.

Permitted: the collection may perform any HTTP method it explicitly defines against the
target environment. These are test actions and authorise nothing else.
