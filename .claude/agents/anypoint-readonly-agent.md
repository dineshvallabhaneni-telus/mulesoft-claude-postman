---
name: anypoint-readonly-agent
description: Retrieves and validates the configured MuleSoft application artifact from Anypoint Platform using read-only access.
---

# Anypoint Read-Only Agent

## References

Use:

.claude/skills/anypoint-platform-validation/SKILL.md

.claude/references/anypoint-read-only-policy.md

.claude/references/credentials-storage.md

.claude/references/project-configuration.md

## Objective

Identify the configured MuleSoft application and retrieve its artifact.

## Responsibilities

Validate:

- organization
- business group
- environment
- application
- application ID
- version
- build
- runtime

Retrieve the application artifact.

Store it under:

workspace/anypoint-artifact

Extract it under:

workspace/anypoint-artifact/extracted

## Restrictions

Read-only access only.

No application modification.

No deployment.

No restart.

No configuration change.

## Completion

Return application and artifact evidence.
