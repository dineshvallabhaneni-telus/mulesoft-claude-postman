---
name: test-report
description: Phase 6 - write the analysis judgement and generate the consolidated Microsoft Word validation report.
---

# Test Report Skill

## Reference

`.claude/references/test-report-schema.md`

## Step 1 — Write `workspace/execution/analysis.json`

Your judgement, in the schema given in `Prompt/prompt.md`. Ground every statement in
the phase 4 and phase 5 evidence files. Never invent test results, and never put
secrets in this file.

Flag changed areas that the collection does not cover — untested change is a genuine
risk.

## Step 2 — Generate

```bash
python3 scripts/generate_report.py
```

Optional: `--output NAME.docx`, or set `REPORT_FILE_NAME`. The default name is
`<application>-<environment>-validation-<UTC timestamp>.docx` in `reports/`.

## What is mechanical and what is yours

| Report part | Source |
|---|---|
| Cover page, sections 1 to 3, appendices A to D | evidence JSON, rendered mechanically |
| Section 1.2 high-level changes | `analysis.json` |
| Section 4 risk and impact | `analysis.json` |
| Section 5 final recommendation | `analysis.json` |

## Reconciliation

The generator overrides `overallValidationResult` when it contradicts the evidence: any
failed test forces `FAIL`, and an unexecuted collection forces `BLOCKED`. Write the
honest value rather than relying on the override.

## Validation

The script re-opens the saved document and confirms all five required sections exist
before exiting zero. Treat a non-zero exit as a failed run, not a warning.

Every test case in the collection appears in Appendix A. No test case is omitted, and
the section 1 counts must reconcile with it.
