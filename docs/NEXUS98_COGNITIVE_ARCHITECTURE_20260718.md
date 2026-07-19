# Nexus98 Cognitive Architecture (2026-07-18)

This document records implementation of the ten cognitive-intelligence
frameworks that compose the internal Nexus98 Cognitive Architecture. They
extend (do NOT replace) the verified foundation and the framework-integration
layer. All are advisory/representational: they model intelligence, they do not
execute actions and they do not change autonomy state. The Supervisor, Router,
Governor, and Guardian remain authoritative.

Package: `core/cognitive/` (11 modules).

## 1. Intent Intelligence (`intent.py`)
- `IntentAnalyzer.analyze()` -> `Intent` with intent type (information/action/
  planning/review/learning/ambiguous/unknown), extracted `Objective`s, ambiguity
  score, confidence, clarification needs + questions, metadata, entities.
- Heuristic classifier (keyword signals) + ambiguity/confidence scoring. Not
  coupled to execution.

## 2. Goal Management (`goals.py`)
- `GoalManager`: goals, subgoals (parent_id), milestones, dependencies,
  priorities, progress (%), interruption/resume via `resume_context()`.
- Persisted `data/goals.json`. Integrates conceptually with Continuity/Planning/
  Memory (advisory; does not call them directly to stay decoupled).

## 3. Planning Intelligence (`planning.py`)
- `PlanningIntelligence` wraps `core.frameworks.planning.PlanningEngine` and
  adds: execution graph + dependency graph, alternative plans, rollback plans,
  checkpoint marking, effort/resource estimation, and critical-path analysis.
- Planning remains strictly advisory — no `execute`/`run` surface.

## 4. Decision Engine (`decision.py`)
- `DecisionEngine`: weighted scoring, hard `Policy` gates, tradeoff analysis,
  confidence (top-gap x inverse-risk), explanation, risk, recommendation.
- `decide_model()` integrates Model Intelligence + a safety policy. Advisory
  only; Governor remains sole autonomy-state writer.

## 5. Context Intelligence (`context.py`)
- `ContextAssembler.assemble()` -> unified `TaskContext`: objective, active
  project, workspace reality, recent activity, architecture state, loaded
  models, available tools, runtime config, strategy. Read/assemble only.

## 6. Knowledge Graph (`knowledge.py`)
- `KnowledgeGraph`: typed nodes (project/file/module/class/tool/model/decision/
  architecture/pattern/task) and relations (depends_on/implements/relates_to/
  contradicts/supersedes/uses/tested_by). Extends Code Memory (kg_node records);
  edges in `data/db/knowledge_graph.json`. Does not replace memory.

## 7. Execution Intelligence (`execution.py`)
- `ExecutionIntelligence.prepare()` -> `ExecutionPlan` with steps, retry
  policies, validation checkpoints, batching, stopping conditions, topological
  sequence. **Prepares only — never executes.** No `execute`/`run_steps`.

## 8. Review Intelligence (`review.py`)
- `ReviewIntelligence` over `core.frameworks.review.ReviewSystem`: specialized
  implementation/code/architecture/regression reviews, lessons learned,
  recommendations, quality scoring per review type. Observational only.

## 9. Learning (`learning.py`)
- `LearningSystem`: passive recording of success/failure/solution/heuristic
  patterns, confidence updates (nudged by observed outcome), reusable
  solutions, evolution summary. **Passive — no self-modifying behavior.** Index
  in `data/db/learning.json` (derived alongside memory DB when db_path given).

## 10. Communication (`comms.py`)
- `CommunicationBus`: in-process pub/sub with standardized `Message` envelopes
  across 13 subsystem channels. Delivers to in-memory subscribers only; failing
  subscribers are isolated. Does NOT replace bridge/API/UI channels.

## Architecture Decisions
- All frameworks use dependency injection (constructor params) over hard-coded
  references; default singletons are provided for convenience.
- Storage is split per concern (goals.json, plans.json, learning.json,
  knowledge_graph.json, reviews.json) — no god-file.
- Cognitive frameworks build on existing subsystems (Planning, Review, Knowledge,
  Memory, Model Intelligence, Tool Registry, Capability Awareness) rather than
  re-implementing them.
- No framework exposes execution or autonomy mutators; Supervisor/Router
  authority preserved.

## Tests (+59)
`test_cog_intent` (8), `test_cog_goals` (7), `test_cog_planning_intel` (4),
`test_cog_decision` (5), `test_cog_context` (3), `test_cog_knowledge_graph` (5),
`test_cog_execution` (7), `test_cog_review` (6), `test_cog_learning` (8),
`test_cog_comms` (7).

## Validation
- Full suite: **268 passed** (baseline 209; +59, 0 failures).
- Protected files (`supervisor.py`, `system_config.json`, `governor.py`)
  mtimes unchanged. No `auto_execute`/autonomy-level change.
- Real `data/db` index files left clean (`{}`); tests use temp paths.
- Checkpoint: `backups/COGNITIVE_20260718_104520/`.

## Remaining Cognitive Gaps
- Cognitive frameworks are not yet wired into a single runtime "cognitive
  loop" (intent -> goal -> plan -> decision -> context -> execution-prep ->
  review -> learning via the comms bus). A coordinator composing them is the
  natural next step.
- P1 `auto_execute` + P2 legacy-path cleanup still blocked at file level
  (no approval / external lock), unchanged by this session.
- No live end-to-end run (would need AutoGen/Ollama); validated via hermetic
  unit tests with fakes/temp stores.
