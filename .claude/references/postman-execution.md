# Postman Execution Reference

## Collection

`postman_collection/`, already present in the workspace. It is never cloned or
downloaded, and it is never modified.

Discovery order inside that directory:

| Artefact | Patterns | Override |
|---|---|---|
| Collection | `*.postman_collection.json`, then `*collection*.json` | `POSTMAN_COLLECTION_FILE` |
| Environment | `*.postman_environment.json`, then `*environment*.json` | `POSTMAN_ENVIRONMENT_FILE` |

Environment discovery prefers a filename containing `TARGET_ENVIRONMENT`, default
`DEV`. Running without an environment file is allowed and is recorded in the report.

## Execution

Newman runs the full collection in its defined order. Every request executes on every
run — the source comparison never selects tests.

Tunable through environment variables:

| Variable | Default | Effect |
|---|---|---|
| `NEWMAN_TIMEOUT_REQUEST` | `60000` | per-request timeout in ms |
| `NEWMAN_DELAY_REQUEST` | `0` | delay between requests in ms |
| `NEWMAN_INSECURE` | `false` | `true` disables TLS verification |
| `NEWMAN_BAIL` | `false` | `true` stops at the first failure |

Newman exiting non-zero because assertions failed is a reportable outcome, not a
framework error.

## Evidence captured

Test case ID, execution order, folder path, request method and URL, request headers
and body, HTTP status and status text, response time, response size, response headers
and body, every assertion with its outcome and failure detail, transport errors, and
the classified result with its reason.

## Redaction and truncation

URLs, headers and bodies pass through the redaction filter. Bearer and Basic tokens,
credentials embedded in URLs, GitHub PAT-shaped strings, and any value whose key looks
like a secret are replaced with `[REDACTED]`.

Bodies are truncated to 4000 characters, and the truncation is stated in place.

## Results

| Result | Condition |
|---|---|
| `PASS` | The request executed and every assertion passed |
| `FAIL` | An assertion failed, or the request errored in transport |
| `SKIPPED` | Every assertion for the request was skipped by the collection |
| `BLOCKED` | The collection could not be executed at all |
| `NOT EXECUTED` | No response was recorded, or the request defines no assertions |

Never infer a PASS. A 200 response with no assertion behind it is not evidence of
correctness, so it is reported as `NOT EXECUTED` with `statusReason` explaining why.

The overall run result is `FAIL` if any test failed, `BLOCKED` if the collection did
not execute, otherwise `PASS`.

## Protection

Not modified by this phase: the collection, the environment file, the MuleSoft source,
or the repository. Writes go only to `workspace/execution/`.

The collection may perform any HTTP method it explicitly defines — GET, POST, PUT,
PATCH, DELETE, HEAD, OPTIONS — against the target environment. These are sanctioned
test actions and do not authorise modifying anything else.

## Output

`workspace/execution/postman-results.json`
