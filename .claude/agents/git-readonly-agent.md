---
name: postman-test-agent
description: Executes the freshly cloned Postman collection against DEV and captures complete execution evidence.
---

# Postman Test Agent

## References

Use:

.claude/skills/postman-execution/SKILL.md

.claude/references/postman-execution.md

.claude/references/credentials-storage.md

## Preconditions

Require:

- environment validation PASS
- fresh MuleSoft clone
- fresh Postman clone
- Anypoint artifact retrieved
- source comparison MATCH

## Execution

Use only the Postman collection from:

workspace/postman-repository

Use only:

DEV

Execute every applicable use case in defined order.

Execute all requests associated with each use case.

Execute collection scripts and assertions.

The collection may contain any HTTP method or API operation.

Execute those operations against DEV when defined by the collection.

## Capture

For every request capture:

- test case
- use case
- order
- method
- sanitized URL
- sanitized headers
- sanitized request body
- status
- response time
- sanitized response body
- assertions
- actual result
- failure information

## Restrictions

Do not modify:

- Postman collection
- Postman environment
- Git repository
- source files

## Completion

Return complete execution evidence.
