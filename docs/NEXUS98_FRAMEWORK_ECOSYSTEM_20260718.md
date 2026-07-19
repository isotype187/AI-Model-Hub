# Nexus98 Framework Ecosystem (2026-07-18)

This document records the implementation of seven architecture-layer frameworks
that extend the verified foundation (Strategy Engine, Code Memory, Continuity,
Tool Registry, Coordination). All frameworks are additive, perform no
autonomy-state mutation, and preserve the Governor/Guardian safety boundaries.

Package: `core/frameworks/` (8 modules).

## 1. WWW / Workspace Reality Continuity (`workspace.py`)
- `WorkspaceReality` JSON store (`data/workspace.json`): projects, components
  (files/modules/services/config), relationship edges (the "web"), system state.
- `register_project`, `register_component`, `link`/`neighbors` (graph),
  `set_state`, `reality_snapshot` (resume view). Corruption-safe load.
- Integrates with Continuity + Code Memory + Project Engine (records reality;
  never writes source files itself).

## 2. Project Intelligence (`project.py`)
- `ProjectIntelligence` extends (does NOT replace) Project Engine.
- `understand_project` (state/health awareness), `record_dependency`
  (dependency awareness), `plan_change` (change planning, separate from
  execution), `note_checkpoint`, `track_progress` (milestone + % progress).
- Intelligence records stored in `data/project_intelligence.json`.

## 3. Model Intelligence (`model.py`)
- `ModelIntelligence` registry reading `config/models.json`.
- `ModelProfile` with strengths/weaknesses, cost_tier, performance_tier,
  availability. `recommend(task, category=, available_only=)` and
  `explain_recommendation`. Word-level task tagging (tokens len>=3) for robust
  suitability scoring. Advisory only — never launches/downloads models.

## 4. Knowledge Architecture (`knowledge.py`)
- `KnowledgeArchitecture` on top of Code Memory.
- Typed capture: `record_decision`, `record_lesson`, `record_architecture`,
  `record_pattern`. Explicit knowledge graph via `link`/`related` (relations:
  relates_to / implements / contradicts / supersedes / depends_on) stored in
  `data/db/knowledge_links.json`. Queries: `lessons`, `patterns`,
  `architecture_records`.

## 5. Planning (`planning.py`)
- `PlanningEngine` + `Plan`/`TaskNode`. Task decomposition, goal tracking,
  milestone planning, dependency tracking (`depends_on`), `ready_tasks`
  (dependency-respecting), `progress` %. Plans persist in `data/plans.json`.
- **Boundary enforced:** planning is strictly separate from execution
  authority; `PlanningEngine` exposes no execute/run surface.

## 6. Evaluation & Review (`review.py`)
- `ReviewSystem` + `Evaluation`. Scored evaluations over weighted dimensions
  (correctness/completeness/safety/clarity/efficiency) -> verdict
  (pass/partial/fail/needs_review). `failures`, `improvement_suggestions`
  (weakest dimensions). Append-style store `data/reviews.json`. Observational
  only; never auto-applies fixes.

## 7. Extension / Plugin (`extension.py`)
- `ExtensionRegistry` + `Extension`. Registers pluggable components with
  metadata, capabilities, hooks, and a lifecycle
  (registered -> enabled -> active -> disabled -> error). `discover`
  (by capability/hook), `capability_summary`. Distinct from Tool Registry:
  Tool Registry catalogs function-level *capabilities of existing tools*;
  Extension Registry manages optional *plugin components* and their lifecycle.
- No extension code is executed by this framework; records only.

## Tests
New framework suites (all temp DB / temp file; real `data/` never touched):
- `test_framework_workspace.py` (7), `test_framework_project.py` (6),
  `test_framework_model.py` (6), `test_framework_knowledge.py` (5),
  `test_framework_planning.py` (6), `test_framework_review.py` (6),
  `test_framework_extension.py` (7) — total **+42 new tests**.

## Validation
- Full suite: **183 passed** (baseline 141; +42, 0 failures).
- Protected files (`supervisor.py`, `system_config.json`, `governor.py`)
  mtimes unchanged. No `auto_execute`/autonomy-level change.
- Checkpoint: `backups/FRAMEWORKS_20260718_101925/`.

## Architecture Decisions
- Frameworks live in a single `core/frameworks/` package for cohesion and
  discovery; each is independently importable.
- Storage is split by concern (workspace.json, project_intelligence.json,
  plans.json, reviews.json, extensions.json, knowledge_links.json) — no single
  god-file, no checkpoint sprawl.
- All frameworks delegate persistence to existing stores where possible
  (Code Memory / MemoryService, Continuity) rather than re-implementing DBs.
- Planning explicitly excludes execution; Extension explicitly excludes running
  extension bodies — both preserve the "Stability before Autonomy" boundary.
