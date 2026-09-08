# MuleSoft Deployment Validation Framework

## Purpose

A reusable, zero-configuration framework that validates a MuleSoft application
change set before or after deployment, and produces a professional Microsoft Word
validation report.

It runs inside an existing GitHub Actions workspace and is invoked headlessly:

```bash
claude -p "$(cat Prompt/prompt.md)"
```

`Prompt/prompt.md` is the operational prompt. This file is the standing policy that
applies to every run.

The framework is generic. It contains no project-specific values and no credentials.

---

# Workspace Contract

Everything the framework needs is already in the workspace when the job starts.

| Path | Contents | Provided by |
|---|---|---|
| repository root | current MuleSoft source under validation | `actions/checkout` |
| `previous_ws/` | previous deployment's MuleSoft source | the calling workflow |
| `postman_collection/` | Postman collection, and environment file if any | the same repository |
| `workspace/execution/` | evidence written by this framework | phases 4 and 5 |
| `reports/` | the final `.docx` report | phase 6 |

Nothing is cloned. Nothing is downloaded. Anypoint Platform is never contacted.

---

# Configuration

There is no configuration file and no credentials file.

Defaults live in `scripts/framework_config.py`. Any of them can be overridden by an
environment variable of the same name, which is how a calling workflow customises a
run:

```yaml
env:
  TARGET_ENVIRONMENT: QA
  PREVIOUS_WORKSPACE: ./baseline
```

`APPLICATION_NAME` is derived from the workspace when not set: `pom.xml` `artifactId`,
then the GitHub repository name, then the workspace directory name.

Secrets are supplied only as environment variables, normally from GitHub Actions
secrets. Never write a secret to a file, a log, or the report.

---

# Mandatory Workflow

Three phases, in this order. Phase numbering is retained from the previous framework
so existing references stay meaningful; phases 1 to 3 no longer exist.

## Phase 4 — Source Comparison

```bash
python3 scripts/source_compare.py
```

Compares the current source against the previous deployment source in `previous_ws/`,
file by file, by content hash. Writes `workspace/execution/source-comparison.json`.

Identifies added, deleted and modified files, and classifies them: Mule flow changes,
API changes, dependency changes, configuration changes, DataWeave changes, tests,
documentation.

A non-zero exit stops the run. Classify it `BLOCKED`.

**A mismatch is not a failure.** Changes are the expected input to this framework —
they are what gets analysed. This phase does not gate phase 5.

## Phase 5 — Postman Testing

```bash
python3 scripts/run_postman.py
```

Executes the **full** Postman collection from `postman_collection/` with Newman and
writes `workspace/execution/postman-results.json`.

Every request in the collection is executed on every run. The phase 4 diff informs the
analysis, never the test selection.

Read the source comparison to interpret the results, not to decide what to run.

## Phase 6 — Analysis and Report

Write `workspace/execution/analysis.json` — your judgement, in the schema given in
`Prompt/prompt.md`. Then:

```bash
python3 scripts/generate_report.py
```

Renders the consolidated Word report into `reports/` and validates it before exiting.

---

# Boundaries

## Read-only

- The MuleSoft source is read-only. Do not modify it.
- `previous_ws/` is read-only.
- The Postman collection and environment file are read-only. Execute them unmodified.
- No Git write operations: no commit, push, merge, rebase, tag, branch create or delete.
- Write only inside `workspace/execution/` and `reports/`.

## Prohibited

- Cloning or fetching any repository.
- Downloading any deployment artifact.
- Contacting Anypoint Platform for any reason.
- Any environment validation phase. Assume the runner is provisioned.
- Deploying, redeploying, restarting or reconfiguring anything.

## Permitted

The Postman collection may perform any HTTP method it explicitly defines — GET, POST,
PUT, PATCH, DELETE, HEAD, OPTIONS — against the target environment. These are test
actions. They do not authorise modifying the repository, the collection, or any
deployed application.

---

# Result Rules

Use only:

```
PASS   FAIL   SKIPPED   BLOCKED   NOT EXECUTED
```

Never infer a PASS. Every result must be backed by actual execution evidence.

A request that was sent but has no assertions defined is `NOT EXECUTED`, with the
reason recorded — a bare 2xx with no validation is not evidence of correctness.

If an individual test fails, capture it and continue with the remaining independent
tests. If a prerequisite prevents execution, classify as `BLOCKED` or `NOT EXECUTED`
with the reason recorded.

Every test case in the collection must appear in the report. No test case may be
silently omitted.

---

# Report

A professional Microsoft Word document in `reports/`, structured per
`.claude/references/test-report-schema.md`:

1. Summary
2. Source Comparison
3. Postman Test Results
4. Risk and Impact Analysis
5. Final Recommendation

Plus appendices: complete test case inventory, per-test execution evidence, detailed
file change log, and execution boundaries.

Sections 1 to 3 and the appendices are generated mechanically from the evidence files.
Section 4, section 5, and the high-level change summary come from your `analysis.json`.

Sensitive values are redacted automatically by `scripts/framework_config.py`. Do not
rely on that alone — do not put secrets into `analysis.json` in the first place.

---

# Chat Output

Do not print the report contents.

The final message must be exactly three lines:

```
Overall Status: <PASS | FAIL | BLOCKED>
Recommendation: <SAFE_TO_PROCEED | PROCEED_WITH_CAUTION | NOT_SAFE>
Report: reports/<generated-file-name>.docx
```
