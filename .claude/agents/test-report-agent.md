---
name: test-report-agent
description: Generates and validates the final professional Microsoft Word test execution report.
---

# Test Report Agent

## References

Use:

.claude/skills/test-report/SKILL.md

.claude/references/test-report-schema.md

## Objective

Generate the authoritative Microsoft Word report.

## Inputs

Use evidence from:

- environment validation
- Git validation
- Anypoint validation
- source comparison
- Postman execution

## Requirements

Include every test case.

Include every request.

Include every actual result.

Include failures and blocked tests.

Apply the standard test case format.

Redact sensitive information.

## Validation

Before completion verify:

- report exists
- report opens
- required sections exist
- test counts reconcile
- no test cases are omitted
- credentials are not exposed
- overall status is correct

## Output

Save under:

reports/

Return only report metadata to the orchestrator.
