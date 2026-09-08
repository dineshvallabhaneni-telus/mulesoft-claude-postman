# Source Comparison Reference

## Sources

| Side | Location | Notes |
|---|---|---|
| Current | repository root of the workspace | checked out by the calling workflow |
| Previous deployment | `previous_ws/` | placed by the calling workflow |

Both are already present. Nothing is cloned, fetched or downloaded, and Anypoint
Platform is never contacted. The previous deployment's *source* is the baseline, not a
deployed artifact.

Override the baseline location with `PREVIOUS_WORKSPACE`.

## Scope

Every file in either tree is compared, except names listed in `COMPARISON_EXCLUDE`,
which by default skips `.git`, `.github`, `.claude`, `.vscode`, `.idea`, `target`,
`node_modules`, `.mule`, `previous_ws`, `workspace`, `reports`, `scripts`, `Prompt`,
`postman_collection` and `.DS_Store`.

Set `MULESOFT_SOURCE_SUBDIRS` to a comma-separated list to restrict the comparison to
specific paths, for example `src,pom.xml`.

## Equality

Files are equal only when their SHA-256 content hashes match.

These are never accepted as evidence of equality:

- filename
- directory structure
- file size
- timestamps
- application or POM version

## What is reported

Per file: status (`ADDED`, `DELETED`, `MODIFIED`), category, impact, content hashes,
and for text files a redacted unified diff with added and removed line counts.

Diffs are capped at `COMPARISON_MAX_DIFF_LINES` lines, default 400, and marked
`truncated` when cut.

## Structured deltas

Beyond line diffs, the comparison parses the changed files:

| Source | Extracted |
|---|---|
| `src/main/mule/**.xml` | flow and sub-flow names, HTTP listener paths and allowed methods, outbound request paths, APIKit references |
| `pom.xml` | dependencies added, removed, and version-changed |
| `.properties`, `.yaml`, `.yml` | property keys added and removed |

These are aggregated into the top-level `behaviourDeltas` object. Read it first — it is
the shortest path to what could actually change behaviour.

## Redaction

Diff text passes through the redaction filter before being written, so a changed
password or token appears as `[REDACTED]` rather than its value. The key name is
retained, because *that a secret changed* is itself relevant to the analysis.

## Result

`IDENTICAL` when no file differs. `CHANGES_DETECTED` otherwise, with
`highestImpact` set to the highest impact level among the changed files.

A result of `CHANGES_DETECTED` is normal. Changes are the input this framework exists
to analyse, and this phase does not gate Postman execution.

## Output

`workspace/execution/source-comparison.json`
