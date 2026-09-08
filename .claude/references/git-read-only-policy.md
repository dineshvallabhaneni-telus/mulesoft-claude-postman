# Git Read-Only Policy

## Scope

Applies to:

- MuleSoft repository
- Postman repository

## Required

Every run must use a fresh clone.

Existing local repositories must not be reused.

## Allowed

- clone
- fetch
- inspect
- log
- status
- branch inspection
- commit inspection
- file listing
- file reading
- diff
- hashing

## Prohibited

- add
- commit
- push
- merge
- rebase
- tag
- branch creation
- branch deletion
- source modification
- configuration modification
- repository administration

## Repository Files

Do not modify files in either cloned repository.

Do not create files inside either repository.

Do not delete files inside either repository.