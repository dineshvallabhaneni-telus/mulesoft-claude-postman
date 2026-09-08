# Postman Execution Skill

## References

Use:

.claude/references/postman-execution.md

## Preconditions

Source comparison must be:

MATCH

## Procedure

1. load the freshly cloned collection
2. load DEV environment
3. verify DEV is active
4. execute collection in defined order
5. execute every applicable use case
6. execute every associated request
7. execute scripts
8. execute assertions
9. capture actual results
10. continue after independent failures

## API Actions

The collection is authoritative.

Any HTTP method or API action explicitly defined by the collection may be executed against DEV.

## Restrictions

Do not modify:

- collection
- environment
- repository
- source