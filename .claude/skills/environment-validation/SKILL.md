# Environment Validation Skill

## Procedure

1. Detect the operating system.
2. Determine whether it is Windows or macOS.
3. Validate required tooling.
4. Determine versions.
5. Identify missing mandatory dependencies.
6. Install missing dependencies using the appropriate platform mechanism.
7. Configure PATH when required.
8. Revalidate all dependencies.

## Minimum Tooling

Evaluate the actual workflow requirements for:

- Git
- Java
- Maven
- Anypoint CLI
- MuleSoft tooling
- Postman CLI
- Node.js
- npm
- Python

Do not install unnecessary software.

## Gate

A mandatory missing dependency blocks the workflow.

## Evidence

Record:

- operating system
- dependency
- version
- path
- installation result
- final status