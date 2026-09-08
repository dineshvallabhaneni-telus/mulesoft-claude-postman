---
name: source-comparison-agent
description: Phase 4. Compares the current MuleSoft source in the workspace against the previous deployment source in previous_ws, and summarises what could affect behaviour.
---

# Source Comparison Agent

## References

`.claude/skills/source-comparison/SKILL.md`
`.claude/references/source-comparison.md`

## Inputs

Current source: the repository root of the GitHub Actions workspace.

Previous deployment source: `previous_ws/`.

Both are already present. Do not clone, fetch or download anything, and do not
contact Anypoint Platform.

## Procedure

Run the comparison:

```bash
python3 scripts/source_compare.py
```

This writes `workspace/execution/source-comparison.json`. A non-zero exit means the
comparison could not run — report it and classify the run `BLOCKED`.

Then read the evidence file and interpret it. Start with `behaviourDeltas`, which
already isolates the changes that can alter runtime behaviour, then consult individual
entries in `changes` for the diffs that matter.

## What to identify

- Added, deleted and modified files
- Mule flow and sub-flow changes
- HTTP endpoint and API changes
- Dependency additions, removals and version changes
- Configuration and property key changes
- DataWeave changes
- Anything else that could alter application behaviour

## Interpretation

Differences are the expected input to this framework, not a failure. This phase does
not block phase 5 — the full Postman collection runs regardless of what changed.

Focus on functional impact. A logging level change and a removed endpoint are not the
same finding, and the report should not treat them alike.

## Output

Return a summary of the change set and its likely functional impact. The raw evidence
stays in `workspace/execution/source-comparison.json` for the report generator.
