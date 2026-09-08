# Configuration Reference

The framework is zero-configuration. There is no config file and no credentials file.

Defaults live in `scripts/framework_config.py`. Any value can be overridden by an
environment variable of the same name, which is how a calling GitHub Actions workflow
customises a run:

```yaml
env:
  TARGET_ENVIRONMENT: QA
  PREVIOUS_WORKSPACE: ./baseline
```

## Identity

| Variable | Default | Notes |
|---|---|---|
| `APPLICATION_NAME` | derived | `pom.xml` `artifactId`, then the GitHub repository name, then the workspace directory name |
| `TARGET_ENVIRONMENT` | `DEV` | Appears on the cover page and biases Postman environment-file discovery |

## Workspace paths

All relative to the workspace root — `GITHUB_WORKSPACE` when set, otherwise the
repository root.

| Variable | Default | Contents |
|---|---|---|
| `CURRENT_WORKSPACE` | `.` | Current MuleSoft source under validation |
| `PREVIOUS_WORKSPACE` | `./previous_ws` | Previous deployment's source, the comparison baseline |
| `POSTMAN_COLLECTION_DIR` | `./postman_collection` | Collection, and environment file if present |
| `EXECUTION_DIRECTORY` | `./workspace/execution` | Evidence JSON written by the framework |
| `REPORT_OUTPUT_DIRECTORY` | `./reports` | The generated `.docx` |

## Postman

| Variable | Default | Notes |
|---|---|---|
| `POSTMAN_COLLECTION_FILE` | auto-discover | Explicit path, tried relative to the collection directory, then the workspace root |
| `POSTMAN_ENVIRONMENT_FILE` | auto-discover | Same resolution |
| `NEWMAN_TIMEOUT_REQUEST` | `60000` | Per-request timeout in ms |
| `NEWMAN_DELAY_REQUEST` | `0` | Delay between requests in ms |
| `NEWMAN_INSECURE` | `false` | `true` disables TLS verification |
| `NEWMAN_BAIL` | `false` | `true` stops at the first failure |

## Comparison

| Variable | Default | Notes |
|---|---|---|
| `MULESOFT_SOURCE_SUBDIRS` | empty | Comma-separated allow-list, e.g. `src,pom.xml`. Empty compares everything not excluded |
| `COMPARISON_EXCLUDE` | see below | Comma-separated path segment names skipped on both sides |
| `COMPARISON_MAX_DIFF_LINES` | `400` | Per-file unified diff cap |

Default exclusions: `.git`, `.github`, `.claude`, `.vscode`, `.idea`, `target`,
`node_modules`, `.mule`, `previous_ws`, `workspace`, `reports`, `scripts`, `Prompt`,
`postman_collection`, `.DS_Store`.

## Report

| Variable | Default | Notes |
|---|---|---|
| `REPORT_FILE_NAME` | derived | Default `<application>-<environment>-validation-<UTC timestamp>.docx` |

## Secrets

Secrets are never stored in this repository. Supply them as environment variables from
GitHub Actions secrets, and reference them from the Postman environment file or the
collection as that collection expects.

Everything the framework writes passes through the redaction filter in
`scripts/framework_config.py`, which masks Bearer and Basic tokens, credentials
embedded in URLs, GitHub PAT-shaped strings, and any value whose key looks like a
password, secret, token, key, credential or passphrase.

Redaction is a safety net, not a licence. Do not print secrets and do not write them
into `analysis.json`.
