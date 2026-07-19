# Nexus98 Codex Handoff 01
# Foundation and Rules

## Purpose

This document defines the non-negotiable foundation rules for Nexus98 development.

## Core Identity

Nexus98 is a local-first AI command center and development environment.

It is not allowed to replace architecture blindly.

All implementation must preserve existing validated systems.

## Development Rules

Before any production modification:

1. Inspect current implementation.
2. Create a checkpoint.
3. Explain intended changes.
4. Apply controlled modifications.
5. Test.
6. Validate.
7. Report results.

## Authority Boundaries

Governor:
- controls autonomous actions
- remains sole autonomy writer

Guardian:
- owns Git
- owns recovery
- owns integrity validation

Nexus98:
- communicates with Guardian
- does not own Git
- does not bypass safety systems

## Prohibited Actions

Never:
- blindly replace old architecture
- create duplicate authority systems
- bypass validation
- modify Guardian ownership
- add uncontrolled autonomy
