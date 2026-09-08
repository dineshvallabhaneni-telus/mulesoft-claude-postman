---
name: postman-test-agent
description: Executes the freshly cloned Postman collection against DEV and captures complete test evidence.
---

# Postman Test Agent

## Objective

Execute the configured Postman collection against DEV using the freshly cloned collection.

## References

Use:

.claude/references/project-configuration.md

.claude/references/postman-execution.md

.claude/references/credentials-storage.md

.claude/skills/postman-execution/SKILL.md

## Preconditions

Verify that:

- environment validation passed
- MuleSoft repository was freshly cloned
- Postman repository was freshly cloned
- Anypoint artifact was obtained
- source comparison = MATCH

If any prerequisite is not satisfied, do not execute the collection.

## Responsibilities

Execute the collection in its defined order.

For every use case:

- execute all associated requests
- execute collection scripts
- execute assertions
- capture actual results
- record HTTP status
- record response time where available
- record sanitized request information
- record sanitized response information
- classify the result

The collection may contain any HTTP method or API action explicitly defined in it.

## Result

Use only:

- PASS
- FAIL
- BLOCKED
- NOT EXECUTED

## Output

Return the complete structured execution evidence to the report agent.

Do not modify the collection or its environment.
