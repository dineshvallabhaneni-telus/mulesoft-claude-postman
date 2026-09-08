# Git Repository Validation Skill

## References

Use:

.claude/references/git-read-only-policy.md

.claude/references/project-configuration.md

## Procedure

For each configured repository:

1. read repository URL
2. read branch
3. default branch to Develop if unspecified
4. ensure destination is appropriate for a fresh clone
5. clone repository
6. verify remote
7. verify branch
8. verify commit SHA
9. verify expected contents

Repositories:

- MuleSoft application
- Postman collection

## Postman

Locate:

- collection
- DEV environment

## Gate

A failed fresh clone blocks downstream processing.