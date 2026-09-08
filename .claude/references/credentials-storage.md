# Credentials Storage Reference

## Preferred Approach

Use enterprise-managed credentials whenever possible.

Preferred order:

1. enterprise secret manager
2. operating-system credential store
3. short-lived authentication
4. local credentials.env

---

## Local Credentials

Fallback:

credentials/credentials.env

This file must never be committed.

---

## Git Credentials

MuleSoft:

MULESOFT_GIT_USERNAME

MULESOFT_GIT_TOKEN

Postman:

POSTMAN_GIT_USERNAME

POSTMAN_GIT_TOKEN

Git credentials must provide repository read-only access.

---

## Anypoint Credentials

ANYPOINT_CLIENT_ID

ANYPOINT_CLIENT_SECRET

The Anypoint identity must have only the permissions required for read-only application inspection and artifact retrieval.

---

## Secret Handling

Never display credentials.

Never place credentials in:

- Word reports
- logs
- chat
- source comparison
- screenshots
- generated documentation

Replace sensitive values with:

[REDACTED]