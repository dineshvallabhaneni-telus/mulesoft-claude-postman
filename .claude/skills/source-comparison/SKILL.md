# Source Comparison Skill

## References

Use:

.claude/references/source-comparison.md

## Procedure

Compare:

workspace/mulesoft-repository

with:

workspace/anypoint-artifact/extracted

Perform a complete inventory.

Compare actual file content.

Do not assume equality based on:

- filename
- directory
- file size
- application version
- timestamps

Check all relevant configuration and source files.

## Result

MATCH:

No relevant differences.

MISMATCH:

One or more relevant differences.

## Gate

MISMATCH blocks Postman execution.