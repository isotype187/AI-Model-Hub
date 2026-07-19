# Nexus98 Codex Handoff 02
# Architecture and Systems

## Purpose

Understand the existing Nexus98 architecture.

## Core Architecture

Major systems:

- main.py entry point
- UI layer
- Supervisor
- Project Engine
- Autonomy Governor
- Memory Service
- Model systems
- Bridge systems
- VS Code integration

## Architecture Principles

Nexus98 uses:

- modular systems
- governed execution
- read-only observation where required
- separated responsibilities

## Guardian Relationship

Guardian remains external.

Nexus98 requests Guardian services.

Guardian controls:

- recovery
- Git
- integrity validation
- known-good states

## Implementation Priority

Foundation stability comes before expansion.
