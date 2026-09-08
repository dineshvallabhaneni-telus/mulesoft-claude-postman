# Anypoint Platform Validation Skill

## References

Use:

.claude/references/anypoint-read-only-policy.md

.claude/references/project-configuration.md

.claude/references/credentials-storage.md

## Procedure

1. authenticate using configured credentials
2. identify configured organization
3. identify business group
4. identify environment
5. identify application
6. validate application identity
7. obtain version/build metadata
8. retrieve application artifact
9. calculate checksum where practical
10. extract artifact

## Storage

Artifact:

workspace/anypoint-artifact

Extracted:

workspace/anypoint-artifact/extracted

## Restrictions

All Anypoint application access is read-only.