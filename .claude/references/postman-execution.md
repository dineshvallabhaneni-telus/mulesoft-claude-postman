# Postman Execution Reference

## Collection

Use only the collection from the freshly cloned Postman repository.

## Environment

Use DEV only.

Do not switch environments.

Do not modify the environment.

## Execution

Execute every use case and request in the collection's defined order.

The collection is authoritative for API actions.

Any HTTP method or API action explicitly defined in the collection may be executed against DEV.

## Evidence

Capture:

- test case ID
- use case
- execution order
- request method
- sanitized URL
- sanitized headers
- sanitized request body
- HTTP status
- response time
- sanitized response body
- assertions
- actual result
- failure details

## Results

PASS

Required validations passed.

FAIL

Required validation failed.

BLOCKED

Execution could not occur because of a prerequisite.

NOT EXECUTED

The test was intentionally not run.

Never infer a PASS.

## Repository Protection

Do not modify:

- collection
- environment
- scripts
- tests
- repository files