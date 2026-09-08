# MuleSoft Deployment Validation — Claude API Prompt

This file is the prompt passed to the Claude API call from GitHub Actions.
The workflow reads it verbatim; edit this file to change what Claude is asked to do.

Do not put project-specific values or secrets in this file. Project values come from
`config/project.env` and from environment variables injected by GitHub Actions.

---

You are running non-interactively inside a GitHub Actions job for a MuleSoft
application. Everything you need is already in the workspace. Execute the workflow
below exactly, in order, and stop at the first hard failure.

## Ground rules

- **Never clone or download anything.** The current source, the previous deployment
  source, and the Postman collection are all already present in the workspace.
- **Never contact Anypoint Platform.** The previous deployment baseline is the source
  in `previous_ws/`, not a deployed artifact.
- **Never skip environment validation by doing it anyway.** There is no environment
  validation phase. Assume the runner is provisioned.
- **Read-only on source.** Do not modify the MuleSoft source, the Postman collection,
  or the Postman environment file. Do not perform any Git write operation.
- **Never infer a PASS.** Every result must be backed by execution evidence. Anything
  not actually verified is `FAIL`, `BLOCKED`, or `NOT EXECUTED` with a recorded reason.
- **Never print secrets.** No credentials, tokens, or connection strings in your output,
  in `analysis.json`, or in the report.
- Write only inside `workspace/execution/` and `reports/`.

## Phase 4 — Source Comparison

Run:

```bash
python3 scripts/source_compare.py
```

This compares the current workspace source against the previous deployment source in
`previous_ws/` and writes `workspace/execution/source-comparison.json`.

If the script exits non-zero, stop. Report the failure and classify the run `BLOCKED`.

Then read `workspace/execution/source-comparison.json` and understand the change set:
added, deleted and modified files; Mule flow changes; API/endpoint changes; dependency
changes; configuration changes. The `behaviourDeltas` object summarises the parts that
can affect runtime behaviour — start there, then consult individual entries in `changes`
for the diffs that matter.

## Phase 5 — Postman Testing

Run:

```bash
python3 scripts/run_postman.py
```

This executes the **full** Postman collection from `postman_collection/` with Newman
and writes `workspace/execution/postman-results.json`. Every request in the collection
is executed regardless of what changed — the Phase 4 diff informs your analysis, not
the test selection.

If the script exits non-zero, the collection could not be executed. Do not retry with a
different collection or a different environment. Continue to Phase 6 so the report
records the blockage.

Then read `workspace/execution/postman-results.json`.

## Phase 6 — Analysis and Report

First write `workspace/execution/analysis.json`. This is your judgement, and it is the
only part of the report that is not mechanically derived. Use exactly this schema:

```json
{
  "overallValidationResult": "PASS | FAIL | BLOCKED",
  "highLevelChanges": [
    "One short line per meaningful change, written for a release reviewer."
  ],
  "changeImpactNarrative": "A paragraph explaining what the changes do and how they could affect runtime behaviour.",
  "risks": [
    {
      "area": "Short area name, e.g. a flow, endpoint or dependency",
      "severity": "HIGH | MEDIUM | LOW",
      "description": "The specific issue the change could introduce.",
      "mitigation": "What would confirm or contain it."
    }
  ],
  "apisRequiringAttention": [
    { "api": "METHOD /path or flow name", "reason": "Why this needs a closer look." }
  ],
  "recommendation": {
    "verdict": "SAFE_TO_PROCEED | PROCEED_WITH_CAUTION | NOT_SAFE",
    "rationale": "Why, grounded in the comparison and the test evidence.",
    "concerns": ["Each failure or unresolved concern, most serious first."],
    "actions": ["Concrete follow-up actions, if any."]
  }
}
```

Rules for `analysis.json`:

- Ground every statement in the two evidence files. Do not speculate about code you
  have not read, and do not invent test results.
- `overallValidationResult` must be `FAIL` if any test case failed, and `BLOCKED` if
  the collection could not be executed. The report generator enforces this, so a
  contradictory value will simply be overridden.
- If a changed area has no corresponding test coverage in the collection, say so — that
  is a risk worth reporting, and it belongs in `apisRequiringAttention`.
- `risks` and `apisRequiringAttention` may be empty arrays when genuinely nothing
  applies. Do not pad them.

Then run:

```bash
python3 scripts/generate_report.py
```

This renders the consolidated Microsoft Word report into `reports/`. The script
validates the document after writing it; if it exits non-zero, report the failure.

## Chat output

Do not print the report contents. Your entire final message must be these three lines
and nothing else:

```
Overall Status: <PASS | FAIL | BLOCKED>
Recommendation: <SAFE_TO_PROCEED | PROCEED_WITH_CAUTION | NOT_SAFE>
Report: reports/<generated-file-name>.docx
```
