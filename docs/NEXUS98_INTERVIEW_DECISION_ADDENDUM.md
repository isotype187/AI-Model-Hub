# Nexus98 Interview Decision Addendum

## Purpose

This document preserves finalized Nexus98 architectural interview decisions for later Constitution integration.

The Constitution remains the authoritative source after integration.

---

# AI Intelligence and Model Selection

## Decisions

Nexus98 automatically selects:

- model
- provider
- agent configuration
- strategy presets

The automatic selection should always be visible to the user.

Example:
Selected Model:
Qwen3-Coder

Reason:
Best compatibility with current coding task

Strengths:

code generation
reasoning
repository understanding

Compatible Agents:

Coding Agent
Debug Agent

User retains override authority.

The user may manually select:

- model
- provider
- agent
- strategy

Automatic selection assists the user but does not remove control.

---

# Strategy System

## Decisions

Strategies are independent intelligence layers.

Multiple compatible strategies may operate together.

Examples:

- Conservative coding
- Documentation first
- Fast iteration
- Deep analysis
- Testing focused
- Security focused

Strategies influence:

- model selection
- agent behavior
- tool usage
- execution approach

Nexus98 should explain major strategy choices.

---

---

# Agent System

## Decisions

Agents are specialized workers within Nexus98.

Agents contain:

- purpose
- capabilities
- tools
- permissions
- memory
- preferred models
- preferred strategies

Architecture:

Hybrid.

Permanent core agents exist for common functions.

Temporary specialized agents may be created for specific tasks.

Complex tasks may use multiple agents working together.

Nexus98 coordinates agents.

Agents do not independently become system authorities.

---

# Agent Memory

## Decisions

Agent memory is hybrid.

Individual agents may maintain specialized knowledge related to their purpose.

Nexus98 maintains the master project memory system.

Agent knowledge should remain connected to approved project memory.

Memory ownership must remain clear.

---

# Tool System

## Decisions

Nexus98 can discover, evaluate, and use tools.

Tool workflow:

1. Search installed capabilities.
2. Search approved external sources.
3. Search GitHub/repositories when appropriate.
4. Recommend available solutions.
5. Create custom tools when necessary.

Custom tool creation requires:

- defined purpose
- permissions
- validation
- testing
- registration

Tool memory tracks:

- usage history
- success rate
- compatibility
- failures
- recommendations

High-risk tools require additional validation.

---

---

# Agent System

## Decisions

Agents are specialized workers within Nexus98.

Agents contain:

- purpose
- capabilities
- tools
- permissions
- memory
- preferred models
- preferred strategies

Architecture:

Hybrid.

Permanent core agents exist for common functions.

Temporary specialized agents may be created for specific tasks.

Complex tasks may use multiple agents working together.

Nexus98 coordinates agents.

Agents do not independently become system authorities.

---

# Agent Memory

## Decisions

Agent memory is hybrid.

Individual agents may maintain specialized knowledge related to their purpose.

Nexus98 maintains the master project memory system.

Agent knowledge should remain connected to approved project memory.

Memory ownership must remain clear.

---

# Tool System

## Decisions

Nexus98 can discover, evaluate, and use tools.

Tool workflow:

1. Search installed capabilities.
2. Search approved external sources.
3. Search GitHub/repositories when appropriate.
4. Recommend available solutions.
5. Create custom tools when necessary.

Custom tool creation requires:

- defined purpose
- permissions
- validation
- testing
- registration

Tool memory tracks:

- usage history
- success rate
- compatibility
- failures
- recommendations

High-risk tools require additional validation.

---

---

# Conversation System

## Decisions

Nexus98 conversations are separate but connected.

Conversation types include:

- project conversations
- personal conversations
- development conversations
- research conversations

Conversations may share approved context.

They must not blindly share all history.

Context sharing should be intentional and governed.

---

# Context Loading

## Decisions

Nexus98 should automatically identify relevant context.

Suggested context may include:

- related architecture decisions
- recent work
- project files
- previous conversations
- relevant documents

The user retains control over context selection.

The system should explain major context choices.

---

# WWW System

## Where Were We

WWW is the continuity system that restores user awareness after interruptions.

WWW should appear after:

- normal shutdown
- Don't Forget activation
- interrupted sessions

WWW should summarize:

- previous work completed
- current task
- decisions made
- unfinished items
- recommended next actions
- system status

WWW should allow the user to quickly continue work.

---

# Don't Forget System

## Decisions

Don't Forget is an emergency continuity action.

Purpose:

Allow the user to immediately preserve current work before leaving unexpectedly.

When activated:

- save current session state
- capture recent work
- create recovery marker
- prepare WWW summary
- integrate with Guardian recovery workflow

Don't Forget is not limited to predefined checkpoints.

It creates an unscheduled recovery point.

---

---

# Recovery System

## Decisions

Recovery points should be modular rather than static.

A recovery point may contain:

- current work state
- affected modules
- memory state
- configuration state
- validation information
- relevant project context

Recovery points should be customizable depending on the situation.

---

# Rolling Known-Good Recovery Point

## Decisions

Guardian maintains a rolling emergency recovery point.

Purpose:

Maintain the last known state where all critical modules were verified functional.

This becomes the emergency rollback target.

The rolling recovery point should:

- update when system health is verified
- preserve validation information
- replace older known-good states
- remain separate from ordinary checkpoints

---

# Guardian Integration

## Decisions

Guardian remains a separate project.

Guardian responsibilities:

- Git commits
- Git pushes
- version control authority
- checkpoints
- recovery points
- validation
- system integrity monitoring

Nexus98 communicates with Guardian.

Nexus98 does not own Git operations.

Guardian may provide:

- recovery requests
- health status
- validation results
- checkpoint management

---

# Guardian Safety Model

## Decisions

Guardian must be inspected and matured before unrestricted autonomous operation.

High-risk actions require:

- validation
- recovery availability
- clear ownership
- user approval when necessary

Guardian is the safety authority, not the intelligence authority.

---

---

# Control Panel

## Decisions

The Control Panel is the central system management interface.

It includes:

- AI status
- model/provider controls
- Guardian status
- Recovery controls
- Memory management
- Bridge controls
- Tool status
- System health

Controls should display:

- current state
- explanation
- available actions
- warnings when applicable

The user retains manual control.

---

# UI Philosophy

## Decisions

Nexus98 uses a chat-first interface.

Default experience:

- primary conversation area
- accessible controls
- progressive complexity

Advanced panels exist but should not overwhelm the default experience.

Panels may be collapsible.

The default state should not hide important functionality.

---

# Adaptive Layout

## Decisions

Nexus98 must remain functional when resized.

Requirements:

- responsive layouts
- scrollable sections when necessary
- preserved usability at different window sizes
- adaptive panel behavior

The entire application should resize cleanly.

---

# Internal Development Environment

## Decisions

Future Nexus98 should allow development from inside Nexus98.

Capabilities:

- integrated VS Code access
- coding workspace
- internal shell
- AI-assisted development

The main chat may act as an operational command interface.

Example:

"Hey Nexus, do this."

Nexus98 interprets intent and performs approved actions.

---

# Self Modification

## Decisions

Nexus98 may eventually assist in modifying itself.

This is a high-risk capability.

Required process:

1. Analyze requested change.
2. Explain proposed modification.
3. Create checkpoint.
4. Apply controlled change.
5. Test.
6. Validate.
7. Report result.

Guardian protection is required.

---

# Memory Philosophy

## Decisions

Memory must preserve knowledge while minimizing storage.

Avoid:

- thousands of old update files
- endless checkpoints
- duplicate historical copies

Prefer:

- database-backed memory
- indexing
- compression
- lifecycle management
- searchable records

Memory should remain functional without unnecessary storage growth.

---

# Code Memory

## Decisions

Every relevant project file should be represented.

Includes:

- Python modules
- JSON
- YAML
- configuration files
- relationships
- dependencies

Purpose:

Allow fast understanding and safe modification of the codebase.

Code Memory is a knowledge system, not a replacement for source control.

---

