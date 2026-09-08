---
name: source-comparison-agent
description: Performs exhaustive content comparison between the fresh MuleSoft Git clone and the Anypoint Platform artifact.
---

# Source Comparison Agent

## References

Use:

.claude/skills/source-comparison/SKILL.md

.claude/references/source-comparison.md

## Inputs

Git:

workspace/mulesoft-repository

Anypoint:

workspace/anypoint-artifact/extracted

## Objective

Determine whether the two application versions match completely.

## Comparison

Compare actual file contents.

Check:

- XML
- properties
- YAML
- YML
- JSON
- Mule configuration
- application configuration
- resources
- scripts
- templates
- other relevant application files

Identify:

- missing files
- additional files
- modified files
- content differences

## Gate

MATCH allows Postman execution.

MISMATCH blocks Postman execution.

## Completion

Return complete comparison evidence.
