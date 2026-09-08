---
name: source-comparison
description: Phase 4 - compare the current MuleSoft source against the previous deployment source already present in the workspace.
---

# Source Comparison Skill

## Reference

`.claude/references/source-comparison.md`

## Procedure

```bash
python3 scripts/source_compare.py
```

Compares the repository root against `previous_ws/` and writes
`workspace/execution/source-comparison.json`.

Both trees are already in the workspace. Never clone, fetch or download, and never
contact Anypoint Platform.

## Comparison rules

Files are compared by SHA-256 of their contents. Filename, directory, size, timestamp
and version number are never treated as evidence of equality.

Text files get a redacted unified diff. Binary files are compared by hash and size.

## Classification

Every changed file is assigned a category and an impact level:

| Category | Impact | Matches |
|---|---|---|
| `DEPENDENCY` | HIGH | `pom.xml`, gradle build files |
| `MULE_FLOW` | HIGH | `src/main/mule/**.xml` |
| `API_SPEC` | HIGH | RAML, and API specs under an `api/` path |
| `DATAWEAVE` | HIGH | `.dwl`, anything under `dwl/` |
| `CONFIGURATION` | MEDIUM | properties and YAML under `src/main/resources`, `mule-artifact.json`, `log4j2.xml` |
| `BINARY` | MEDIUM | jars, archives, images, keystores |
| `TEST` | LOW | `src/test/**` |
| `DOCUMENTATION` | LOW | `.md`, `.txt` |
| `OTHER` | MEDIUM | everything else |

## Structured deltas

Beyond raw diffs, the script extracts:

- Mule flow and sub-flow names added or removed
- HTTP listener paths and allowed methods added or removed
- Maven dependencies added, removed, or version-changed
- Property and YAML keys added or removed

These are aggregated into `behaviourDeltas` — read that first.

## Result

`IDENTICAL` when nothing changed, `CHANGES_DETECTED` otherwise.

Changes are the expected input to this framework. This phase does not gate phase 5.
