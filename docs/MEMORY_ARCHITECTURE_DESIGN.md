# Nexus98 Memory System Architecture Design

> Status: Design Review (no implementation)
> Scope: Long-term autonomous AI operating memory for Nexus98
> Companion code: `core/memory.py` (current minimal JSON store), `core/db.py` (existing SQLite precedent)

This document defines the intended memory architecture for Nexus98. It is a design artifact only. Nothing here changes running code until a follow-up implementation phase is approved.

---

## 1. Purpose and Constraints

Nexus98 is evolving from a development assistant into a local AI development environment with controlled autonomous workflows. Memory is not chat history; it is the system's persistent operating substrate.

Hard constraints observed from the current codebase:

- Today memory lives in `core/memory.py`, a single `Memory` class that appends opaque dicts to `agent_memory.json` (cwd-relative). No locking, no atomic write, no query/update/delete, no IDs.
- A SQLite database already exists at `data/db/models.db` (`core/db.py`), proving SQLite is an accepted, dependency-free storage option in this project.
- Configuration convention is JSON files in `config/` (e.g. `settings.json`), not env-heavy setup.
- The runtime assumes a single fixed install root `D:\Nexus98` (`ROOT = Path(r"D:\Nexus98")` in many modules). Path configurability should be additive, not replace the working assumption.

Design goals: persistent, structured, auditable, controlled, and scalable from one assistant to many agents/projects.

---

## 2. Architecture Diagram

```
                         ┌────────────────────────────────────────┐
                         │            Memory Service API          │
                         │  (single import surface, versioned)    │
                         │  store() query() update() forget()     │
                         │  verify() export() import()           │
                         └───────────────┬────────────────────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            │                            │                             │
   ┌────────▼─────────┐      ┌──────────▼─────────┐       ┌──────────▼─────────┐
   │  Storage Layer   │      │  Index / Retrieval  │       │  Integrity / Audit │
   │  (replaceable)   │      │  (pluggable)        │       │  (always on)       │
   │  v1: SQLite      │      │  v1: structured SQL │       │  - validation      │
   │  v2: + vector    │      │  v2: + semantic     │       │  - change log      │
   │  v3: + graph     │      │  v3: + knowledge gr │       │  - backups         │
   └────────┬─────────┘      └──────────┬─────────┘       │  - verification     │
            │                           │                 └──────────┬─────────┘
            └───────────────────────────┴─────────────────────────────┘
                                         │
                         ┌───────────────▼────────────────┐
                         │     Memory Layers (logical)    │
                         │  1 Identity / Preference       │
                         │  2 Project                    │
                         │  3 Episodic                   │
                         │  4 Semantic                   │
                         │  5 Operational                │
                         │  6 Decision (critical)        │
                         └────────────────────────────────┘

Consumers: Supervisor, Orchestrator/Agents, Project Engine, CLI/API, Recovery tooling.
```

The key idea: **one API, logical layers, a replaceable storage backend, and an always-on integrity/audit layer.** The first implementation only fills v1 of each box; later phases swap internals without touching callers.

---

## 3. Data Model Proposal

### 3.1 Core memory record (one row)

| Field                | Type      | Required | Notes |
|----------------------|-----------|----------|-------|
| `memory_id`          | str (UUID)| yes      | Primary key, immutable |
| `type`               | enum      | yes      | One of the 6 layers (see 3.2) |
| `category`           | str       | no       | Free sub-grouping, e.g. `routing`, `architecture` |
| `content`            | text/json | yes      | The actual memory payload |
| `source`             | str       | yes      | Who/what created it (agent name, `user`, `system`, `migration`) |
| `project`            | str       | no       | Project scope; default `nexus98` |
| `timestamp_created`  | ISO-8601  | yes      | Set on create |
| `timestamp_updated`  | ISO-8601  | yes      | Updated on every mutation |
| `confidence`         | float 0-1 | yes      | Default 1.0 for explicit human/system writes |
| `importance`         | int 1-5   | yes      | Drives ranking and decay priority |
| `verification_status`| enum      | yes      | `unverified` / `verified` / `disputed` / `archived` |
| `last_verified`      | ISO-8601  | no       | When last confirmed still true |
| `expiration_policy`  | enum      | no       | `never` / `ttl_days:N` / `until_verified` |
| `access_control`     | enum      | no       | `shared` (default) / `agent_private` / `restricted` |
| `related_memories`   | list[str] | no       | memory_ids this links to (edges for future graph) |
| `version`            | int       | yes      | Increment on each update |
| `update_history`     | json      | yes      | Append-only list of `{ts, field, old, new, by}` |

This schema merges the requested field list with auditability (version + update history) and future graph support (`related_memories`).

### 3.2 Memory layers (the `type` enum)

1. **identity** — stable user preferences: communication style, coding/formatting/workflow/tool preferences. Never stores secrets; `access_control` defaults `restricted`.
2. **project** — Nexus98 knowledge: architecture decisions, file locations, components, milestones, failed approaches, recovery points, discoveries.
3. **episodic** — events: what changed, when, what was tested, result. A development journal.
4. **semantic** — learned knowledge: concepts, explanations, reusable patterns/solutions.
5. **operational** — current state: active tasks, phase, pending decisions, blockers, running services, health. High-churn; naturally decays.
6. **decision** — critical. Always requires `alternatives_considered`, `reason`, `risks_accepted`, `authority`, `date`. Stored with `verification_status=verified` and high `importance`.

### 3.3 Backward compatibility note

Existing `agent_memory.json` entries are dicts with `task`/`agent`/`response`. A migration maps:
- `agent` -> `source`
- `task` -> `category`/`content` prefix
- `response` -> `content`
- `type` -> `episodic`
This preserves all current data during migration (Phase 5).

---

## 4. Storage Recommendation

**Phase 1 (recommended first storage): SQLite**, reusing the proven `data/db/` location pattern from `core/db.py`.

Rationale:
- Zero new dependencies (stdlib `sqlite3` already used in-repo).
- Gives atomic transactions, concurrent-read/single-writer safety, indexing for structured queries, and an integrity path (`PRAGMA integrity_check`).
- JSON column for `content`/`update_history`/`related_memories` keeps the flexible payload while SQL indexes serve retrieval.
- Easy, safe backup (copy the file; `VACUUM INTO`).

**Designed-for-replacement components** (interface stays stable):
- A `StorageBackend` abstraction so v2 can add a vector store (e.g. Chroma, already present in `.venv` via `autogen_ext.memory.chromadb`) for semantic similarity, and v3 can add a graph layer for `related_memories`.
- The Memory Service API never references SQLite directly; it talks to the backend interface. Swapping backends is a config change, not a rewrite.

**What stays simple initially:** file layout, single-process writer with a lock, plain SQL queries. No external services, no network, no new runtime processes.

---

## 5. Retrieval Design

Built in tiers so we never "search all memories":

- **Tier 1 (v1): exact + structured filtering** — by `type`, `category`, `project`, `source`, `verification_status`; range filters on `timestamp_created`; `confidence >=`, `importance >=`; `related_memories` membership. Pure SQL.
- **Tier 2 (v2): semantic similarity** — embed `content`, store vectors, support "architecture decisions about routing, last 90 days, high confidence." Hybrid: structured SQL pre-filter, then vector re-rank.
- **Tier 3 (v3): knowledge graph** — traverse `related_memories` edges for relationship queries ("what decisions depend on the Ollama routing decision?").

Ranking: `score = importance * w1 + confidence * w2 + recency_decay(ts) * w3`, with `verification_status=verified` boosted and `archived`/`disputed` demoted. Recency decay is a pure function so it is testable and reversible.

---

## 6. Scaling Roadmap

| Phase | Storage | Retrieval | Scope | Replaceable? |
|-------|---------|-----------|-------|--------------|
| 1 | SQLite (single writer + lock) | Structured SQL | 1 assistant, 1 project | backend swappable |
| 2 | SQLite + vector index | SQL prefilter + semantic | semantic layer matures | add vector backend |
| 3 | + graph store | + relationship traversal | multi-agent, multi-project | add graph backend |
| 4 | sharded by `project` | hybrid symbolic+semantic | autonomous workflows, planning | horizontal split |

Each phase is additive: the API and data model do not change; only backends and retrievers are added behind interfaces.

---

## 7. Migration Strategy

- **Versioned schema**: `schema_version` table. `Memory.migrate()` runs idempotent forward steps only.
- **Backward/forward safe**: existing `agent_memory.json` imported via the 3.3 mapping; original file kept as `agent_memory.json.migrated`.
- **No destructive moves**: migrations copy-then-flag; the source remains until a verification pass confirms the target. Rollback = restore the copied file.
- **Corruption handling**: on load, run `PRAGMA integrity_check`; if failed, fall back to the latest `.bak` snapshot and log. Memory must survive corrupted sessions and failed migrations.
- **Verification gates**: after migration, assert row counts and checksum parity with the source export before deleting backups.

---

## 8. Security Model

- **Prevent uncontrolled growth**: `importance`/`expiration_policy` drive archival; operational memories auto-expire; a `VACUUM`/prune job runs on threshold.
- **Prevent duplicates**: deterministic dedupe on `(type, category, content_hash)`; `store()` detects near-duplicates and links rather than inserts.
- **Prevent false permanence**: `verification_status` starts `unverified` for model-generated memories; only `user`/`system`/explicit verify can set `verified`. Disputed memories are quarantined, not deleted.
- **Prevent accidental sensitive storage**: `identity` layer schema forbids secret-shaped fields; a scanner flags values matching credential patterns and refuses to persist them.
- **Prevent silent modification**: every mutation appends to `update_history` and bumps `version`; no in-place blind overwrite. Controlled = tracked, reviewable, reversible.
- **Access control**: `shared` (default), `agent_private` (one agent), `restricted` (identity, human-only). Multi-agent sharing is safe because writes are serialized through the single writer + lock and every write is attributed to `source`.

---

## 9. Conflict and Decay Handling

- **Conflicting memories**: never overwrite. New write with same key creates a new record; existing one flips to `disputed` and `related_memories` links them. Resolution is an explicit `verify()` choosing the survivor.
- **Decay / archival**: a scoring job lowers effective rank as `last_verified` ages past `expiration_policy`. Operational memories expire by TTL; durable layers (decision, project) only archive when superseded by a newer, verified record.
- **Multi-agent safety**: single serialized writer; each agent writes under its own `source`; reads are concurrent. Agent-private memories are invisible to others via the API filter.

---

## 10. Implementation Phases (for later approval)

1. **Memory Service API + SQLite backend** — `store/query/update/forget/verify`, schema v1, single-writer lock, integrity check, migration from `agent_memory.json`. Keep `core/memory.py` `Memory` class as a thin shim for backward compatibility.
2. **Retrieval tier 1** — structured filters, ranking function, CLI/API read access.
3. **Audit & security** — `update_history`, dedupe, verification gates, sensitive-field scanner, backup/prune jobs.
4. **Integration** — wire into Supervisor/Orchestrator so agents read/write their layer; recovery tooling uses verification snapshots.
5. **Tier 2 semantic** — add vector backend behind the same interface.
6. **Tier 3 graph + multi-project sharding** — for autonomous, multi-agent operation.

This design satisfies every stated future requirement (persistence, structure, auditability, control, multi-agent, semantic/graph retrieval, migration safety, security) while keeping Phase 1 small and the storage/retrieval layers explicitly designed for later replacement.

---

## 11. Phase 1 Implementation Boundary Review (APPROVED)

Direction accepted. Phase 1 is the minimal reliable foundation that replaces the fragile `agent_memory.json` store. It is deliberately scoped to remove risk, not to deliver the full roadmap.

### 11.1 Goal

Replace the fragile `agent_memory.json` append-only approach with a reliable, persistent memory foundation that is safe to build on.

### 11.2 In Scope (only)

**1. Memory Service interface**

A single import surface exposing exactly:

- `store()` — create a new memory record.
- `query()` — retrieve records by structured filters.
- `update()` — modify an existing record (bumps version, appends `update_history`).
- `delete()` / `forget()` — remove or archive a record.
- `verify()` — set/confirm `verification_status`.
- `export()` — serialize all records (for backup/portability).
- `import()` — load records from an export.

**2. Storage backend: SQLite only**

- Single backend implementation.
- Reuse the existing `data/db/` location convention from `core/db.py`.
- No vector database, no embeddings, no knowledge graph, no multi-agent memory sharing, no autonomous memory creation.

**3. Database requirements**

- **Schema versioning** — a `schema_version` table; forward-only, idempotent migrations.
- **Migration support** — `migrate()` runs pending steps only.
- **Integrity checks** — `PRAGMA integrity_check` on open; fail safe to backup.
- **Atomic writes** — single transactions per operation; no partial commits.
- **Backup before migration** — copy the DB file before any schema change.

**4. Memory record requirements (minimum fields)**

- `memory_id` (UUID, primary key)
- `category`
- `content`
- `source`
- `created_at`
- `updated_at`
- `confidence`
- `importance`
- `verification_status`

(Additional v1 columns `type`/`project`/`related_memories`/`version`/`update_history` are permitted as additive schema, but the nine above are the mandatory minimum.)

**5. Preserve existing memory (migration from `agent_memory.json`)**

The migration must:

- **never delete the original** `agent_memory.json`.
- **create a backup copy** (e.g. `agent_memory.json.bak`) before import.
- **validate imported records** (required fields present, JSON well-formed) and skip/log invalid ones.
- **provide a rollback path** — restoration of the original file and DB backup returns the system to pre-migration state.

Mapping (backward compatible): `agent` -> `source`, `task` -> `category`, `response` -> `content`, `type` -> `episodic` (default).

**6. Testing requirements before expansion**

Must pass before any Phase 2+ work:

- create memory
- retrieve memory
- update memory
- delete / archive memory
- restart persistence (data survives process restart)
- database integrity check
- failed migration recovery (corrupt source / failed step -> rollback, original intact)

### 11.3 Explicitly Out of Scope (Phase 1)

- Vector database, embeddings, semantic similarity.
- Knowledge graph / `related_memories` traversal.
- Multi-agent memory sharing beyond single-writer attribution.
- Autonomous (model-driven) memory creation.
- Ranking/decay jobs, pruning, sensitive-field scanner (API present, jobs deferred).
- Tiers 2/3 retrieval and multi-project sharding.

### 11.4 Phase 1 Acceptance

Phase 1 is complete when the seven tests above pass, the SQLite backend passes `integrity_check`, existing `agent_memory.json` data is preserved with a rollback path, and all access goes through the `Memory Service` interface (no caller reads `agent_memory.json` directly).
