---
name: postman-execution
description: Phase 5 - execute the full Postman collection already present in the workspace and capture redacted evidence.
---

# Postman Execution Skill

## Reference

`.claude/references/postman-execution.md`

## Procedure

```bash
python3 scripts/run_postman.py
```

Runs the full collection from `postman_collection/` with Newman and writes
`workspace/execution/postman-results.json`.

## Discovery

The collection is the first match for `*.postman_collection.json`, then
`*collection*.json`, under `postman_collection/`.

The environment is the first match for `*.postman_environment.json`, then
`*environment*.json`, preferring a filename containing `TARGET_ENVIRONMENT`.

Override either with `POSTMAN_COLLECTION_FILE` or `POSTMAN_ENVIRONMENT_FILE`.

## Scope

The **entire** collection runs on every invocation. The phase 4 diff shapes the
analysis and the risk section, never the test selection.

## Restrictions

Do not modify the collection, the environment file, or the source. Do not clone or
download the collection — it is already in the workspace.

The collection may perform any HTTP method it explicitly defines against the target
environment. These are test actions and are permitted.

## Result classification

| Result | Meaning |
|---|---|
| `PASS` | Every assertion for the request passed |
| `FAIL` | An assertion failed, or the request errored in transport |
| `SKIPPED` | Every assertion was skipped by the collection |
| `BLOCKED` | The collection could not be executed at all |
| `NOT EXECUTED` | No response recorded, or the request has no assertions defined |

Never infer a PASS. A request that returned 200 but defines no assertions is
`NOT EXECUTED`, with the reason recorded in `statusReason`.

## Redaction

URLs, headers, request bodies and response bodies are redacted before being written.
Bodies are truncated to 4000 characters.
