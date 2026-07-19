# Nexus98 Architecture Interview Decision Records

## Purpose

This document contains finalized architecture decisions created during the Nexus98 design interview process.

It exists as a decision source for the Nexus98 Constitution.

Rules:

- Decisions override assumptions.
- No architecture should be invented without approval.
- Guardian and Nexus98 responsibilities must remain separated.
- Future implementation must follow these decisions.

---

# 1. Core Philosophy

## Decision

Nexus98 is a hybrid AI companion and command center.

Primary principles:

- Chat-first interface.
- Automatic intelligence selection.
- User override always available.
- Progressive complexity.
- Adaptive workspace.
- Long-term continuity.

---

# 2. Nexus98 and Guardian Separation

## Decision

Nexus98 and Guardian remain separate projects.

Nexus98:

- intelligence layer
- orchestration
- user interaction
- AI routing
- tools
- conversations

Guardian:

- integrity layer
- Git authority
- recovery authority
- health monitoring
- checkpoints
- validation

Nexus98 must never become the Git authority.

---

# 3. Guardian Philosophy

Guardian exists to ensure Nexus98 remains healthy and operational.

Guardian responsibilities:

- background monitoring
- rolling known-good recovery point
- automatic checkpoints
- recovery validation
- intervention when required

Behavior:

Low risk:
- repair automatically
- report afterward

High risk:
- notify user
- present options
- wait for approval

---

# 4. Memory Philosophy

Memory must remain useful without creating thousands of stale files.

Requirements:

- database-first storage
- compressed historical knowledge
- lifecycle management
- searchable context
- minimal storage footprint

---

# 5. Code Memory

Code Memory stores machine-readable understanding of:

- Python modules
- JSON
- YAML
- configuration
- relationships
- dependencies

Purpose:

Allow Nexus98 to quickly understand and modify code safely.

Guardian maintains authoritative history.

Nexus98 uses the knowledge.

---

# 6. Model Intelligence

Nexus98 automatically selects:

- model
- provider
- agent
- strategies

User can override.

Provider system:

Unified local/cloud abstraction.

Supported concepts:

- Ollama
- OpenRouter
- OpenAI
- Anthropic
- Kimi
- future providers

Recommendations include:

- strengths
- weaknesses
- compatible agents
- strategy compatibility

---

# 7. Agent System

Agents are specialized workers.

Agents have:

- purpose
- capabilities
- tools
- permissions
- memory

System:

Hybrid.

Core agents always exist.

Temporary specialized agents may be created.

Complex tasks use multiple cooperating agents.

---

# 8. Tool System

Nexus98 can:

- discover tools
- evaluate tools
- recommend tools
- create custom tools when necessary

Tool permissions are dynamic.

Tool memory tracks:

- usefulness
- success rate
- compatibility

Guardian validates risky changes.

---

# 9. Conversation System

Conversations are separate but connected.

Features:

- project conversations
- personal conversations
- shared approved context
- automatic context suggestions

WWW:

Where Were We?

Appears after:

- normal startup
- Don't Forget
- interrupted sessions

---

# 10. Development Environment

Nexus98 eventually contains:

- VS Code integration
- shell
- coding workspace
- AI development assistance

Self modification:

Allowed only through governed workflow.

Process:

Analyze

Proposal

Checkpoint

Implementation

Testing

Validation

---

# 11. Control Panel

Control panel:

- adaptive
- accessible
- non-intrusive

Controls include:

- AI status
- Bridge
- Mouse tools
- Guardian
- Recovery
- Memory
- System state

Every control requires:

- label
- status
- hover explanation
- automatic refresh

---

# 12. Recovery

Recovery is modular.

Recovery points contain:

- current work
- system state
- relevant modules
- validation information

Don't Forget:

Creates an emergency continuity point.

Includes:

- session save
- recovery marker
- WWW briefing preparation

---

# End of Decision Records
