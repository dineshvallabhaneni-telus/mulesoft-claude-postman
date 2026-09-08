Execute the complete MuleSoft API validation and Postman test-report workflow defined by this project's CLAUDE.md.

First read and follow:

- .claude/CLAUDE.md
- config/project.env
- the required referenced skills and reference files

Do not ask me to repeat configuration already present in config/project.env.

Perform the workflow end-to-end.

Before proceeding, validate the local machine and all required dependencies.

Get the local MuleSoft repository and Postman repository 

Treat both repositories as strictly READ-ONLY.

Do not modify, commit, push, merge, rebase, tag, create, delete, rename, or otherwise write to either repository.

Validate the configured MuleSoft application in Anypoint Platform and retrieve its corresponding artifact using READ-ONLY access.

Do not modify, deploy, restart, stop, start, delete, or change the Anypoint application or its configuration.

Extract the Anypoint artifact outside the Git repository.

Perform the complete source comparison between the freshly cloned MuleSoft repository and the extracted Anypoint artifact.

Do not proceed to Postman execution unless the source comparison is a complete MATCH.

If there is a mismatch, stop testing, record the differences, generate the Word report, and report BLOCKED in the final chat status.

If the source comparison matches, execute the freshly cloned Postman collection against DEV only.

Do not switch to another Postman environment.

Do not modify the Postman collection or environment.

Execute every applicable use case, request, script, assertion, and API action defined by the collection in its defined order.

The Postman collection is authoritative for the API actions to execute. This includes any HTTP methods such as GET, POST, PUT, PATCH, DELETE, HEAD, or OPTIONS when explicitly defined by the collection.

Capture actual execution evidence for every request and test case.

Continue with independent test cases after failures where technically possible.

Generate the final professional Microsoft Word test execution report according to:

.claude/references/test-report-schema.md

The report must include all test cases and requests, with no omissions.

Include application details, repository details, branches, commit SHAs, Anypoint version/build information, source comparison results, DEV environment confirmation, execution order, request details, HTTP status codes, response evidence, assertions, PASS/FAIL results, failures, blocked tests, observations, deviations, metrics, traceability, security controls, and final overall status.

Redact all credentials, tokens, secrets, authorization values, and other sensitive information.

Save the final report under the configured reports directory.

Validate the generated Word document before completion.

Do not provide the detailed test results in the chat.

After the workflow completes, return only a concise high-level status containing:

- Overall Status
- Source Comparison Status
- Total Tests
- Passed
- Failed
- Blocked
- Not Executed
- Report File Path

Do not modify the framework files unless a workflow failure requires it to complete the requested task. If a framework change would be required, stop and report the issue instead of changing the framework.
