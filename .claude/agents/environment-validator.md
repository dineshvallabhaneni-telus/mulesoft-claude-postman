---
name: environment-validator
description: Validates the local development environment before the MuleSoft and Postman workflow begins.
---

# Environment Validator

## References

Use:

.claude/skills/environment-validation/SKILL.md

## Objective

Validate the local machine before performing application validation.

## Responsibilities

- detect operating system
- determine Windows or macOS
- validate required dependencies
- determine installed versions
- install missing mandatory dependencies when required
- configure PATH where required
- verify installed tools

## Completion

Do not report success until every mandatory dependency is verified.

Return a structured environment validation result for the report.
