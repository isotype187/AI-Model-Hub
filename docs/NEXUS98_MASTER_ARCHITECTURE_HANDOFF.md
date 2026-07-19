# Nexus98 Master Architecture Handoff v2

## Purpose

This document defines the current vision, architecture decisions, constraints, and future development direction for Nexus98.

This document exists to preserve design intent between ChatGPT architecture sessions, Codex implementation sessions, and future development.

---

# 1. Project Identity

## Current Project

Nexus98

Historical origin:

AI Model Hub

Migration:

AI Model Hub → Nexus98

Important:

Nexus98 currently contains historical AI Model Hub references.

Do not perform blind replacement.

Migration should be intentional and verified.

---

# 2. Vision

Nexus98 is intended to become:

A local-first AI operating environment capable of managing:

- conversations
- models
- providers
- agents
- projects
- tools
- code
- memory
- documentation
- workflows

while maintaining:

- safety
- recoverability
- continuity
- user control

---

# 3. Core Architecture

Nexus98 consists of:

## User Interface Layer

Responsible for:

- interaction
- dashboards
- conversations
- controls
- visualization


## Intelligence Layer

Responsible for:

- model routing
- agent selection
- strategy selection
- context selection


## Execution Layer

Responsible for:

- tasks
- tools
- coding
- workflows


## Memory Layer

Responsible for:

- knowledge
- code understanding
- continuity


## Governor

Responsible for:

- autonomy levels
- permissions
- execution safety


## Guardian (Separate Project)

Responsible for:

- health
- recovery
- backups
- Git
- maintenance

---

# 4. Guardian Separation

IMPORTANT:

Guardian currently exists as a separate project.

Guardian is NOT currently merged into Nexus98.

Integration is TBD.

Possible future models:

## External Guardian

Preferred initial model:

Nexus98 communicates with Guardian through controlled interfaces.

## Hybrid

Guardian remains separate but gains Nexus connectors.

## Full Merge

Future possibility only.

---

# 5. Guardian Responsibilities

Guardian owns:

## Git

Guardian manages:

- commits
- pushes
- history
- rollback

Nexus98 may:

- search GitHub
- download tools
- inspect repositories

Nexus98 does NOT own Git operations.


## Recovery

Guardian manages:

- checkpoints
- recovery points
- last known good state


## Health

Guardian monitors:

- Nexus98 health
- dependencies
- tests
- failures


## Memory Maintenance

Guardian manages:

- cleanup
- compression
- duplicate removal

---

# 6. Autonomy Model

Hybrid autonomy.

## Safe

Automatic:

- analysis
- searching
- reports
- suggestions


## Medium Risk

Approval required:

- code modifications
- configuration changes
- restructuring


## High Risk

Guardian protection required:

- Governor changes
- Guardian changes
- security changes
- recovery changes

---

# 7. Model Router

Nexus98 automatically selects:

- provider
- model
- local/cloud
- strategy

User can override.

Dropdowns should show:

- model information
- strengths
- weaknesses
- compatible agents
- recommended use cases

---

# 8. Strategy System

Multiple strategies can be active simultaneously.

Examples:

- Fast
- Accurate
- Coding
- Research
- Creative
- Safety First
- Cost Efficient

---

# 9. Conversation System

Separate conversations:

Examples:

- Personal Assistant
- Coding
- Nexus Development
- Research
- Planning
- Guardian
- Custom


Conversations can share approved context.

---

# 10. UI Vision

Default startup:

Chat interface.

Main window:

Large central conversation area.

Displays:

- input
- output
- execution results
- summaries


Secondary information:

Optional panels:

- logs
- diagnostics
- backend status

---

# 11. Future Integrated Development

Long-term goal:

Nexus98 should be able to:

- edit itself
- run shell commands
- access VS Code functionality
- manage projects internally

---

# 12. Toolbar

Required:

- mode selector
- dashboard selector
- Guardian button
- model selector
- provider selector
- strategy selector
- documents
- memory
- settings
- session controls

---

# 13. Control Panel

Required controls:

- AI toggle
- Bridge toggle
- Mouse tool toggle
- Agent status
- Guardian status
- Recovery controls
- Memory controls

Controls should:

- be labeled clearly
- avoid clutter
- support hover explanations

---

# 14. WWW System

Where Were We system.

Triggered by:

- proper shutdown
- Don't Forget button


Purpose:

Restore user context.

Contains:

- current task
- recent decisions
- system status
- unfinished work
- user intent


---

# 15. Don't Forget

Manual emergency context save.

Creates:

- recovery point
- memory update
- WWW summary

---

# 16. Memory System

Memory must preserve knowledge, not clutter.

Avoid:

Thousands of checkpoint files.

Use databases and indexes.


Memory categories:

- Active Memory
- Knowledge Memory
- Code Memory
- Recovery Memory
- Archive
- Cache


---

# 17. Code Memory

Stores understanding of:

- Python modules
- JSON
- YAML
- configurations

Tracks:

- functions
- classes
- dependencies
- relationships
- summaries
- hashes


Source files remain authoritative.

---

# 18. Documents

Nexus98 Documents section:

Contains:

- architecture
- roadmap
- decisions
- changelog
- Guardian documentation
- memory documentation
- tool library


---

# 19. Current Development Status

Completed:

- autonomy dashboard
- UI refactor foundation
- view separation
- test stabilization

Current:

UI redesign planning.

No major UI implementation should begin until design specification is complete.

---

# 20. Immediate Codex Tasks

Codex should currently perform:

## Task 1

Create architecture inventory.

Document:

- current modules
- dependencies
- entry points
- UI structure
- backend structure


## Task 2

Create future migration map.

Document:

Current:

main_window.py

Future:

modular UI architecture


## Task 3

Create extension analysis.

Identify:

- where model router belongs
- where memory database belongs
- where Guardian interface belongs
- where mode switching belongs


## Task 4

Create risk report.

Identify:

- hardcoded paths
- technical debt
- fragile modules
- future conflicts


## Task 5

Do NOT:

- rewrite UI
- merge Guardian
- alter autonomy logic
- change workflows
- modify production behavior

---

# Development Rule

Before implementation:

checkpoint

analyze

document

approve

implement

validate
