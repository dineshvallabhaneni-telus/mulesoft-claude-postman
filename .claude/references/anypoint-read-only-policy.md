# Anypoint Platform Read-Only Policy

## Allowed

- application lookup
- application metadata inspection
- version inspection
- build inspection
- runtime inspection
- environment inspection
- artifact retrieval
- artifact download

## Prohibited

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
- deployment modification

## Artifact

Store outside the Git repository.

Artifact:

workspace/anypoint-artifact

Extraction:

workspace/anypoint-artifact/extracted

## Security

The Anypoint identity must enforce read-only access.

Instructions alone are not a security boundary.