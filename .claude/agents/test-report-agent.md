---
name: test-report-agent
description: Phase 6. Writes the analysis judgement file and generates the consolidated Microsoft Word validation report.
---

# Test Report Agent

## References

`.claude/skills/test-report/SKILL.md`
`.claude/references/test-report-schema.md`

## Inputs

```
workspace/execution/source-comparison.json    phase 4 evidence
workspace/execution/postman-results.json      phase 5 evidence
```

## Step 1 — Write the judgement

Write `workspace/execution/analysis.json` using the schema in `Prompt/prompt.md`:
`overallValidationResult`, `highLevelChanges`, `changeImpactNarrative`, `risks`,
`apisRequiringAttention`, `recommendation`.

This is the only part of the report that is not mechanically derived. Everything in it
must be grounded in the two evidence files. Do not speculate about code you have not
read and do not invent test results.

If a changed area has no corresponding coverage in the collection, say so — untested
change is a real risk and belongs in `apisRequiringAttention`.

Do not put secrets in this file.

## Step 2 — Generate the report

```bash
python3 scripts/generate_report.py
```

Sections 1 to 3 and all appendices are rendered mechanically from the evidence.
Sections 4 and 5 and the high-level change list come from `analysis.json`.

The overall result is reconciled against the evidence: any test failure forces `FAIL`,
and an unexecuted collection forces `BLOCKED`, regardless of what `analysis.json`
claims.

## Validation

The script re-opens the written document and verifies the five required sections are
present before exiting zero. A non-zero exit means the report is not usable — report
the failure rather than claiming success.

Confirm before finishing:

- the report exists in `reports/`
- every collection test case appears in Appendix A
- the counts in section 1 reconcile with Appendix A
- no credentials appear in the document

## Output

Return only the report path, the overall status and the recommendation. Never print
the report contents.
