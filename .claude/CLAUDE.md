# MuleSoft Postman Test Report Automation

## Purpose

This project provides a reusable, configuration-driven framework for validating a MuleSoft application against its Git local folder, validating the corresponding application artifact from Anypoint Platform, executing a Postman collection against DEV, and generating a professional Microsoft Word test execution report.

The framework is reusable across multiple MuleSoft projects.

Project-specific information must come from:

config/project.env

Credentials must come from the configured secure credential mechanism.

Do not hard-code project-specific values in this file.

---

# Workspace

The VS Code workspace root is the current project directory.

Example:

C:\Projects\MyApiTesting\

All relative paths are resolved from the workspace root.

---

# Configuration

Read:

config/project.env

before starting the workflow.

The configuration contains:

- MuleSoft Git repository URL
- MuleSoft Git branch
- MuleSoft application name
- Anypoint Platform identifiers
- Anypoint environment
- Postman Git repository URL
- Postman Git branch
- Postman collection path
- Postman DEV environment path
- workspace directories
- report output directory

If a required configuration value is missing, stop and report the missing configuration.

Do not guess project-specific values.

---

# Credentials

Use:

credentials/credentials.env

only when a secure enterprise credential mechanism is not available.

Never expose credentials in:

- chat
- logs
- reports
- source comparisons
- screenshots
- generated files

See:

.claude/references/credentials-storage.md

---

# Mandatory Workflow

Execute the workflow in this order.

## Phase 1 — Environment Validation

Use:

environment-validator

Validate the operating system and required tools.

Do not continue until all mandatory dependencies are available and verified.

---

## Phase 2 — Fresh Git Clones

Use:

use an existing local repository  and ask the local location for Mulesoft and postman collection folders

Validate:
1. Mulesoft application repositories
2. postman collection

---

## Phase 3 — Anypoint Platform

Use:

anypoint-readonly-agent

Locate the configured MuleSoft application in Anypoint Platform.

Retrieve the corresponding application artifact.

Only read operations are permitted.

Do not modify the application.

Do not deploy.

Do not restart.

Do not change configuration.

---

## Phase 4 — Source Comparison

Use:

source-comparison-agent

Compare:

workspace/mulesoft-repository

against:

workspace/anypoint-artifact/extracted

The comparison must be exhaustive.

A complete MATCH is required.

If there is any mismatch:

- stop Postman execution
- classify testing as BLOCKED
- include the comparison result in the report

---

## Phase 5 — Postman Testing

Only execute this phase after source comparison is:

MATCH

Use:

postman-test-agent

The Postman collection must come from the freshly cloned Postman repository.

Use DEV only.

Do not modify the Postman collection.

Do not modify the Postman environment.

Execute all API actions defined by the collection.

This includes any HTTP method or API operation explicitly defined in the collection.

Examples include:

- GET
- POST
- PUT
- PATCH
- DELETE
- HEAD
- OPTIONS

API write operations defined by the Postman collection are test actions against DEV and are permitted.

They do not authorize modification of the Postman repository, Git repository, or Anypoint application.

---

## Phase 6 — Report

Use:

test-report-agent

Generate the final Microsoft Word document.

The Word document is the authoritative test result.

The report must contain all executed and non-executed test cases.

No test case may be silently omitted.

---

# Read-Only Boundaries

Git repositories are READ-ONLY.

No Git write operations are permitted.

Do not:

- commit
- push
- merge
- rebase
- tag
- create branches
- delete branches
- modify repository files

The MuleSoft source repository must not be modified.

The Postman repository must not be modified.

---

# Anypoint Platform Boundary

Anypoint Platform application access is READ-ONLY.

Allowed:

- application lookup
- metadata inspection
- version inspection
- build inspection
- runtime inspection
- artifact retrieval

Prohibited:

- deploy
- redeploy
- restart
- stop
- start
- delete
- update
- configuration modification
- property modification
- runtime modification

The Anypoint identity itself must have appropriate read-only permissions.

---

# Postman Boundary

Postman collection execution is allowed.

The collection may perform any API action explicitly defined in the collection against DEV.

The collection itself must not be modified.

The Postman environment must not be modified.

Only the DEV environment may be used.

---

# Test Result Rules

Use:

PASS
FAIL
BLOCKED
NOT EXECUTED

Never infer a PASS.

Every result must be supported by actual execution evidence.

---

# Failure Handling

If an individual Postman use case fails, capture the failure and continue with subsequent independent use cases where technically possible.

If a prerequisite prevents testing, classify affected tests as BLOCKED or NOT EXECUTED as appropriate.

---

# Report

The final report must be a professional Microsoft Word document.

Use the structure defined in:

.claude/references/test-report-schema.md

The report must include:

- application details
- repository details
- branches
- commit SHAs
- Anypoint version/build information
- source comparison
- DEV environment confirmation
- complete test inventory
- execution order
- request details
- responses
- HTTP status codes
- assertions
- PASS/FAIL
- failures
- observations
- deviations
- execution metrics
- final overall status

Sensitive information must be redacted.

---

# Chat Output

The detailed test report must not be displayed in the chat.

The final Word document is the detailed output.

The chat response should contain only a high-level status, such as:

Overall Status: PASS
Report: reports/<report-name>.docx

or:

Overall Status: FAIL
Report: reports/<report-name>.docx

or:

Overall Status: BLOCKED
Report: reports/<report-name>.docx
