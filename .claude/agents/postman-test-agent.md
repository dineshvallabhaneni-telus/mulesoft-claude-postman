---
name: postman-test-agent
description: Phase 5. Executes the full Postman collection already present in the workspace and captures complete, redacted execution evidence.
---

# Postman Test Agent

## References

`.claude/skills/postman-execution/SKILL.md`
`.claude/references/postman-execution.md`

## Input

The collection in `postman_collection/`, already present in the workspace. The
environment file, if the collection directory contains one, is auto-discovered and
preferred by target environment name.

Do not clone or download the collection. Do not modify the collection or the
environment file.

## Procedure

```bash
python3 scripts/run_postman.py
```

This runs the **full** collection with Newman and writes
`workspace/execution/postman-results.json`.

Every request in the collection is executed on every run. The phase 4 source
comparison informs how results are interpreted and what is flagged as risk — it never
decides which tests run.

Newman exiting non-zero because tests failed is a reportable outcome, not a framework
error. The script handles that. A non-zero exit from the script itself means the
collection could not be executed at all: record the blockage and continue to phase 6
so the report captures it.

## Evidence captured per test case

Test case ID, execution order, folder, method, URL, request headers and body, HTTP
status, response time and size, response headers and body, every assertion and its
outcome, transport errors, and the classified result.

Requests, responses and headers are redacted before they are written.

## Results

Use only `PASS`, `FAIL`, `SKIPPED`, `BLOCKED`, `NOT EXECUTED`.

Never infer a PASS. A request that was sent but has no assertions defined is
`NOT EXECUTED` with the reason recorded — a bare 2xx with no validation proves nothing.

## Output

Return the summary counts and the failures. The full evidence stays in
`workspace/execution/postman-results.json`.
