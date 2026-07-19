# Nexus98 - Code Memory Specification

Status: DESIGN SPECIFICATION ONLY (documentation; no implementation, no production changes).
Source of truth: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md (v2),
docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md, and the existing core/memory_service.py
(MemoryService Phase 1 SQLite architecture) + docs/MEMORY_ARCHITECTURE_DESIGN.md.
Constraints: Tkinter-only UI (no new UI deps); SQLite only (stdlib sqlite3, no new deps);
source files remain authoritative; code memory is derived/index, never a second source of truth.

This specification defines a Code Memory subsystem: a structured, queryable understanding of the
Nexus98 codebase (files, modules, functions/classes, dependencies, relationships, hashes, versions,
decisions, docs) built on top of the existing memory_service. It does not change code, config, tests,
Guardian, or dependencies.

## 1. Purpose of Code Memory

Code Memory gives Nexus98 and its agents a persistent, machine-readable map of the codebase so the
system can reason about code without re-reading every file each turn.

- Handoff #16-17 require DB-backed memory and a code-understanding index (functions, classes,
  dependencies, relationships, summaries, hashes). Today memory_service stores generic records only;
  there is NO code-memory index.
- Intent: preserve knowledge, not clutter (handoff #16). Avoid thousands of checkpoint files; use
  databases and indexes.
- Consumers benefit:
  - Supervisor / Project Engine: pre-check impact of a proposed edit (which symbols/files a change touches).
  - UI: explain a module, show a dependency trace, locate related code (future chat/control surfaces).
  - AI agents: answer 'find function X', 'explain module Y', 'trace dependency Z' without full-file reads.
  - Future Guardian integration: recovery/health checks can validate that indexed hashes match
    live files (integrity), and 'explain this change' summaries can be attached to recovery points.
- Non-goals: Code Memory does NOT store executable code, secrets, or autonomy state. It never writes
  source files. It is read-mostly and rebuildable from source at any time.

## 2. Data Model

Code Memory is modeled as a set of related entities, all keyed to the authoritative source file.
Each entity carries a stable id, location, integrity hash, and understanding metadata. Entities are
linked by relationships (imports, calls, contains, references, documents).

### 2.1 files
- Identity: project, repo-relative file_path, language (python/json/yaml/config/other).
- State: source_hash (sha256 of full file content at index time), last_indexed, indexed_by,
  importance, index_status (indexed/stale/failed).
- Understanding: summary (optional, authored by agent or static heuristic), decision_refs,
  doc_refs.
- A file is the anchor: every module/function/class/decision/doc link resolves to a file.

### 2.2 modules (top-level Python module / package __init__)
- Identity: file_path, module_name (qualified, e.g. core.autonomy.governor), language.
- Location: start_line/end_line (module docstring / top scope).
- Understanding: summary, public_api (list of exported symbol ids), responsibilities.
- Relationship: contained_in = file; contains = functions/classes.

### 2.3 functions / classes
- Identity: symbol_id (UUID), qualified_name (e.g. core.autonomy.governor.request_level_change),
  name, symbol_type (function/class/method/config_key), language.
- Location: file_path, start_line, end_line, parent_symbol (class for methods; null for module-level).
- Integrity: source_hash (file), code_hash (sha256 of the symbol body only -> change detection).
- Understanding: summary, docstring, parameters (json for functions), signature, complexity_hint,
  dependencies (json list of referenced symbol ids / import strings), importance, confidence.
- Relationship: defined_in = file/module; calls/references = other symbols; contained_in = parent.

### 2.4 dependencies
- Directed edges between symbols/files: edge_type in {imports, calls, references, inherits,
  contains, documents, decides}.
- Source symbol_id/file -> target symbol_id/file/path, plus context (line range, qualifier).
- Stored as rows so 'trace dependency' is a graph walk, not a grep.

### 2.5 relationships
- Beyond code edges, semantic relationships link code to non-code memory:
  - documents: symbol <-> architecture/design doc (doc_refs).
  - decides: symbol <-> decision memory (decision_refs) — why this code exists / constraint it enforces.
  - related: loose similarity edges (computed, low confidence) for 'locate related code'.

### 2.6 hashes
- source_hash: per-file sha256. Drives incremental indexing (skip unchanged files).
- code_hash: per-symbol sha256 of the normalized symbol body. Drives symbol-level change detection
  (re-summarize only changed symbols).
- Stored, never recomputed on read. Used by Guardian integrity checks and by change detection.

### 2.7 versions
- Index is versioned independently of source control. Each index run stamps last_indexed + an
  index_run_id. Symbols carry the index_run_id of their last (re)index so a whole run can be
  invalidated/rotated. Mirrors memory_service's schema_version + per-record ersion pattern.

### 2.8 decisions
- Decisions are NOT duplicated from the decision memory layer; Code Memory holds decision_refs
  (memory_ids of type='decision') pointing at the canonical decision record. A code symbol may cite
  one or more decisions (e.g. governor.py cites the autonomy-safety decision). This keeps the
  'why' auditable and single-sourced in memory_service.

### 2.9 documentation links
- doc_refs point at docs/ files (path + optional section anchor). Enables 'explain module' to surface
  the governing design doc, and lets the UI cross-link code <-> architecture intent.
- A documents relationship edge connects symbol <-> doc path.

## 3. SQLite Schema Proposal

Built on the existing memory_service SQLite conventions: WAL journal mode, schema_version table,
forward-only idempotent migrations, JSON columns for flexible payloads, and soft-delete (forget())
rather than hard DELETE. Proposed new tables live in the SAME database (data/db/memory.db) so the
single-SQLite mandate (handoff #16) and the existing backup/migration tooling are preserved. A
separate code_memory.db sibling is permitted only if a future approved decision splits storage.

    -- versioning (reuse memory_service pattern) -------------------------------
    CREATE TABLE IF NOT EXISTS schema_version ( version INTEGER PRIMARY KEY );

    -- index run bookkeeping ------------------------------------------------
    CREATE TABLE IF NOT EXISTS code_index_runs (
        run_id          TEXT PRIMARY KEY,
        project         TEXT NOT NULL,
        started_at      TEXT NOT NULL,
        finished_at     TEXT,
        status          TEXT NOT NULL,           -- running/done/partial/failed
        files_scanned   INTEGER NOT NULL DEFAULT 0,
        files_indexed   INTEGER NOT NULL DEFAULT 0,
        symbols_indexed INTEGER NOT NULL DEFAULT 0,
        indexed_by      TEXT NOT NULL
    );

    -- files ----------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS code_files (
        file_path     TEXT NOT NULL,
        project       TEXT NOT NULL DEFAULT 'nexus98',
        language      TEXT NOT NULL,
        source_hash   TEXT NOT NULL,
        last_indexed  TEXT NOT NULL,
        run_id        TEXT NOT NULL,
        indexed_by    TEXT NOT NULL,
        importance    INTEGER NOT NULL DEFAULT 3,
        index_status  TEXT NOT NULL DEFAULT 'indexed',  -- indexed/stale/failed
        summary       TEXT,
        PRIMARY KEY (project, file_path)
    );

    -- symbols (functions / classes / methods / modules / config keys) ------
    CREATE TABLE IF NOT EXISTS code_symbols (
        symbol_id      TEXT PRIMARY KEY,
        project        TEXT NOT NULL DEFAULT 'nexus98',
        file_path      TEXT NOT NULL,
        language       TEXT NOT NULL,
        symbol_type    TEXT NOT NULL,     -- module/function/class/method/config_key
        name           TEXT NOT NULL,
        qualified_name TEXT NOT NULL,
        parent_symbol  TEXT,              -- class id for methods
        start_line     INTEGER,
        end_line       INTEGER,
        source_hash    TEXT NOT NULL,     -- file hash at index time
        code_hash      TEXT NOT NULL,     -- symbol body hash (change detection)
        summary        TEXT,
        docstring      TEXT,
        parameters     TEXT,              -- JSON list
        signature      TEXT,
        dependencies   TEXT,              -- JSON list of symbol ids / import strings
        run_id         TEXT NOT NULL,
        last_indexed   TEXT NOT NULL,
        confidence     REAL NOT NULL DEFAULT 1.0,
        importance     INTEGER NOT NULL DEFAULT 3,
        deleted        INTEGER NOT NULL DEFAULT 0
    );

    -- dependency / relationship edges --------------------------------------
    CREATE TABLE IF NOT EXISTS code_edges (
        edge_id     TEXT PRIMARY KEY,
        project     TEXT NOT NULL DEFAULT 'nexus98',
        source_kind TEXT NOT NULL,        -- symbol/file/doc/decision
        source_ref  TEXT NOT NULL,        -- symbol_id or file_path or memory_id or doc path
        target_kind TEXT NOT NULL,
        target_ref  TEXT NOT NULL,
        edge_type   TEXT NOT NULL,        -- imports/calls/references/inherits/contains/documents/decides/related
        context     TEXT,                 -- JSON: line range, qualifier
        confidence  REAL NOT NULL DEFAULT 1.0,
        run_id      TEXT NOT NULL
    );

    -- cross-links to non-code memory (decisions / docs) --------------------
    CREATE TABLE IF NOT EXISTS code_memory_links (
        symbol_id   TEXT NOT NULL,
        link_kind   TEXT NOT NULL,        -- decision/doc
        target_ref  TEXT NOT NULL,        -- memory_id (decision) or doc path
        note        TEXT,
        PRIMARY KEY (symbol_id, link_kind, target_ref)
    );

    -- indexes (mirror memory_service indexing style) -----------------------
    CREATE INDEX IF NOT EXISTS idx_cf_project_path   ON code_files(project, file_path);
    CREATE INDEX IF NOT EXISTS idx_cf_source_hash    ON code_files(source_hash);
    CREATE INDEX IF NOT EXISTS idx_cs_qualified      ON code_symbols(qualified_name);
    CREATE INDEX IF NOT EXISTS idx_cs_file           ON code_symbols(file_path);
    CREATE INDEX IF NOT EXISTS idx_cs_parent         ON code_symbols(parent_symbol);
    CREATE INDEX IF NOT EXISTS idx_cs_language       ON code_symbols(language);
    CREATE INDEX IF NOT EXISTS idx_cs_code_hash      ON code_symbols(code_hash);
    CREATE INDEX IF NOT EXISTS idx_ce_source         ON code_edges(source_ref);
    CREATE INDEX IF NOT EXISTS idx_ce_target         ON code_edges(target_ref);
    CREATE INDEX IF NOT EXISTS idx_ce_type           ON code_edges(edge_type);

Lifecycle discipline: code_symbols uses soft-delete (deleted=1) like memory_service.forget(); the
index run can mark all symbols from a stale run_id as deleted in one transaction and re-insert current
ones, keeping history for audit/rollback.

## 4. Indexing System

### 4.1 AST parsing
- Python: stdlib st module. Walk AST to extract Module/ClassDef/FunctionDef/AsyncFunctionDef,
  Assign (for module-level config keys), and decorators. Capture name, qualified_name, lineno/end_lineno,
  docstring (ast.get_docstring), arguments (signature), and intra-file references (Name/Attribute nodes).
- JSON/YAML: parse via json/PyYAML; each top-level key becomes a config_key symbol; nested keys optional.
- Other: store as a file-level record only (no symbol breakdown) until a parser exists.
- No third-party parser needed; stays dependency-free per handoff constraint.

### 4.2 Incremental updates
- Pre-scan: compute source_hash for each candidate file (config/ + core/ + ui/ + tools/ + integrations/
  + api/ + bridge/ by default; scoped per project).
- Skip files whose source_hash equals the stored code_files.source_hash (unchanged -> no symbol re-parse).
- For changed files, re-parse and upsert symbols; new run_id stamps the batch.
- Index runs are checkpointed (a new code_index_runs row) so a failed run does not corrupt a good index.

### 4.3 Change detection
- File-level: source_hash differs -> file is stale; re-index its symbols.
- Symbol-level: code_hash (symbol body) differs -> only that symbol needs re-summarization; unchanged
  symbols keep their existing summary/confidence (no redundant LLM/agent work).
- After a write, Project Engine (see Section 6) notifies Code Memory with the affected file_path(s);
  indexing scopes to just those files (fast, targeted) rather than a full sweep.

### 4.4 Prioritization
- Importance scores drive what gets agent-authored summaries vs. static-only:
  - High importance (4-5): core engine, autonomy, supervisor, project_engine, memory_service -> agent
    summary + dependency resolution.
  - Medium (3): tools, integrations, ui views -> static summary, lazy agent summary on query.
  - Low (1-2): tests, scripts, backups -> index metadata only, no summary.
- Prioritization reduces token cost: only high-value symbols consume agent summarization budget.

## 5. Memory Lifecycle

Code Memory follows the handoff #16 lifecycle (Active / Archive / Compressed / Deleted) and reuses
memory_service's verification_status + soft-delete semantics.

- Active: current, indexed, source_hash matches live file. Queryable and surfaced to agents/UI.
  Symbols from the latest successful run_id are Active.
- Archived: symbols/files from an older run that are still historically useful (e.g. for 'what changed'
  or recovery context). Marked verification_status='archived' rather than deleted; retained for audit.
- Compressed: when a file/symbol has not been touched and is low importance for N runs, collapse its
  verbose summary into a short stub (keep hashes + edges). Compression is Guardian-owned per handoff
  (#5 memory maintenance) once Guardian exists; until then Nexus98 may compress locally with a logged,
  approval-gated action. Compression never removes hashes/edges (those are needed for integrity).
- Deleted: source file removed or symbol no longer present -> soft-delete (deleted=1) like
  memory_service.forget(). Record preserved for rollback; hard DELETE only via migration/cleanup with
  a checkpoint. Stale-run symbols are soft-deleted in bulk at the start of a new run.

Lifecycle invariant: Active records always reflect the live source (hash-consistent). Any divergence
marks the record Stale and triggers re-index.

## 6. Integration Points

- Supervisor: before run_action_task proposes an edit, query code_symbols/code_edges for the target
  file_path/symbol to enumerate affected symbols and downstream dependents. Feeds the existing
  build_task_plan / validate_task_plan step with impact context. Read-only; Supervisor never writes
  Code Memory directly.
- Project Engine: the SOLE file-mutation authority. After a validated write (post-validate, pre-history
  log), Project Engine emits a 'reindex' notification for the changed file_path(s). Code Memory reacts
  by incrementally re-indexing only those files (Section 4.3). This keeps the index fresh without a
  full sweep and without Code Memory ever performing the write itself. Integration is a governed hook,
  not a new permission.
- UI: future chat-first / control-panel surfaces can call read-only Code Memory queries:
  'explain module', 'trace dependency', 'find function', 'locate related code' (Section 7). The UI
  requests; it never writes Code Memory. Observability stays read-only, consistent with
  ui.autonomy_dashboard.snapshot() and the cross-cutting UI invariants.
- AI agents: agents (orchestrator team) read Code Memory to ground responses, reducing full-file reads
  and token use. Agents may PROPOSE a summary/decision link update via the governed action path
  (Project Engine proposal or a memory_service store), never by direct DB mutation outside the API.
- Guardian (future): Code Memory is Nexus98-side and read/write by Nexus98; Guardian's role is recovery
  and maintenance. Future integration: Guardian's health check can compare code_files.source_hash
  against a known-good inventory (mirroring Guardian's snapshot_engine SHA256 inventory) to detect
  tampering; Guardian-owned compression/dedup of low-value records aligns with handoff #5. Nexus98
  requests these via the Guardian client; Guardian owns execution. No Git or recovery writes live in
  Nexus98.

## 7. Search Capabilities

All searches are read-only SQL/JSON queries over code_symbols / code_files / code_edges. Examples:

- find function: by name/qualified_name (exact or LIKE), optionally filtered by language/symbol_type/
  file_path. e.g. find 'request_level_change' -> core.autonomy.governor.request_level_change.
- explain module: retrieve the module symbol + summary + public_api (exported symbol ids) + doc_refs,
  rendered as a plain-language summary for chat/UI.
- trace dependency: graph walk over code_edges (edge_type in imports/calls/references/inherits) from a
  symbol/file to its upstream sources and downstream dependents; returns the edge chain with context.
- locate related code: combine dependency edges + 'related' semantic edges + shared decision/doc links
  to surface code that touches the same decision or doc, even across unrelated modules.
- by decision: list all symbols citing a decision memory_id (code_memory_links link_kind='decision').
- by doc: list all symbols documenting a docs/ path (edge_type='documents').
- by hash: look up a symbol/file by source_hash/code_hash (integrity + change detection queries).

## 8. Security Boundaries

- Code Memory stores NO secrets, credentials, autonomy state, or executable payloads. It holds
  structural metadata + summaries only.
- Source files remain authoritative. Code Memory is derived/index and fully rebuildable; a corrupted
  index is regenerated, never trusted over source.
- Write access is restricted to the Code Memory service API (mirroring memory_service single import
  surface). Supervisor/UI/agents read; only the indexing pipeline (triggered by Project Engine hooks)
  writes, and only via that API.
- Indexing never executes indexed code. AST parsing is static; no import/eval of target modules (avoids
  running untrusted code during indexing).
- Autonomy state is out of scope: Code Memory does not read or write supervisor.auto_execute or
  system_config.json. The Governor remains the sole autonomy writer (handoff #6, UI invariants).
- Soft-delete + schema_version + WAL (from memory_service) provide auditability and crash safety;
  index runs are checkpointed so a partial run cannot corrupt a good index.
- Path handling must use the future config_manager/base-path resolution (per the intelligence report's
  HIGH-priority debt) rather than hardcoded D:\Nexus98, so Code Memory is portable.

## 9. Migration Strategy

- Phase 0 (this spec): documentation only; no code, config, or DB changes.
- Bootstrap migration: add the code_* tables via a forward-only, idempotent migration in memory_service
  (new SCHEMA_VERSION). Reuses _apply_migrations() pattern; backs up the DB before applying (memory_service
  already supports backup-before-migration).
- Backfill: first full index run populates code_files/code_symbols/code_edges for the default scope
  (config/ core/ ui/ tools/ integrations/ api/ bridge/). Marked with one run_id; old/partial data
  soft-deleted.
- Coexistence: legacy generic memories in the memories table are untouched; Code Memory is additive
  (new tables). No migration of existing records required.
- Retirement of dual memory backends (memory.py vs memory_service.py) is a SEPARATE debt item; Code
  Memory depends only on memory_service (the canonical SQLite store).
- Rollback: because indexing is soft-delete + run-scoped, a bad run is reversed by deleting its run_id
  batch; the DB file itself is restorable from the pre-migration backup.

## 10. Implementation Phases

Each phase follows the handoff Development Rule:
checkpoint -> analyze -> document -> approve -> implement -> validate.

- Phase 1 - Schema + migration: add code_* tables to memory_service (new SCHEMA_VERSION), indexes,
  soft-delete. No behavior change to existing memory API. Validate via import-smoke + integrity_check.
- Phase 2 - Indexer core: AST parser (Python) + JSON/YAML parser; full-scan backfill with run_id
  bookkeeping; source_hash/code_hash computation. Validate on a sampled subset; confirm hashes stable.
- Phase 3 - Incremental + hooks: source_hash skip logic; Project Engine reindex hook (governed);
  change detection at file + symbol level. Validate that an edit re-indexes only changed files.
- Phase 4 - Edges + links: build dependency edges (imports/calls/references/inherits/contains);
  decision/doc cross-links (code_memory_links). Validate graph walk for 'trace dependency'.
- Phase 5 - Search API: read-only query methods (find/explain/trace/locate/by-decision/by-doc/by-hash)
  on the Code Memory service. Unit tests with a temp DB (pytest TMPDIR workaround already documented).
- Phase 6 - Consumer wiring: Supervisor impact pre-check (read-only); future UI query surfaces; agent
  read access. No write paths opened to consumers.
- Phase 7 - Lifecycle + Guardian seam: archived/compressed/deleted transitions; compression gated and
  logged; define the Guardian health/integrity integration contract (read-only hash compare). Guardian
  execution remains Guardian-owned.

Deferral note: UI surfaces and self-editing capabilities (handoff #11) remain HIGH risk and are
implemented only after foundations + the frozen GUI spec are approved. Code Memory indexing is
medium-risk foundation work that unblocks them.

*End of specification. No production files were modified.*
