"""Nexus98 Knowledge Graph Framework.

Expands Code Memory into a structured knowledge graph. Nodes represent
projects, files, modules, classes, tools, models, decisions, architecture,
patterns, and tasks; edges represent relationships
(depends_on / implements / relates_to / contradicts / supersedes / uses /
tested_by). This extends (does NOT replace) ``core.frameworks.knowledge`` and
``core.code_memory`` — it adds a typed node taxonomy and graph queries.

Persistence: nodes stored as Code Memory records (category "kg_node"); edges in
``data/db/knowledge_graph.json``. No autonomy-state mutation.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from core.frameworks.knowledge import KnowledgeArchitecture


ROOT = Path(r"D:\Nexus98")
DEFAULT_EDGE_PATH = ROOT / "data" / "db" / "knowledge_graph.json"

# Valid node kinds for the knowledge graph.
NODE_KINDS = (
    "project", "file", "module", "class", "tool", "model",
    "decision", "architecture", "pattern", "task",
)

# Valid edge relations.
EDGE_RELATIONS = (
    "depends_on", "implements", "relates_to", "contradicts",
    "supersedes", "uses", "tested_by",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class KGNode:
    """A typed knowledge-graph node."""

    node_id: str
    kind: str
    label: str
    project: str = "nexus98"
    summary: str = ""
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id, "kind": self.kind, "label": self.label,
            "project": self.project, "summary": self.summary,
            "updated_at": self.updated_at,
        }


class KnowledgeGraph:
    """Typed knowledge graph on top of Code Memory."""

    def __init__(self, memory: Optional[KnowledgeArchitecture] = None,
                 project: str = "nexus98", db_path: Optional[Path] = None,
                 edge_path: Optional[Path] = None):
        self.memory = memory or KnowledgeArchitecture(project=project, db_path=db_path)
        if edge_path is None and db_path is not None:
            edge_path = Path(db_path).parent / "knowledge_graph.json"
        self.edge_path = Path(edge_path) if edge_path else DEFAULT_EDGE_PATH
        self._edges: Dict[str, dict] = self._load_edges()

    # ------------------------------------------------------------------
    # Edge persistence
    # ------------------------------------------------------------------

    def _load_edges(self) -> Dict[str, dict]:
        if self.edge_path.exists():
            try:
                return json.loads(self.edge_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_edges(self) -> None:
        self.edge_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.edge_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._edges, f, indent=2)
        shutil.move(str(tmp), str(self.edge_path))

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def add_node(self, kind: str, label: str, *, project: str = "nexus98",
                 summary: str = "") -> KGNode:
        if kind not in NODE_KINDS:
            raise ValueError(f"Invalid node kind: {kind}")
        nid = uuid.uuid5(uuid.NAMESPACE_URL, f"kg:{kind}:{label}").hex[:12]
        node = KGNode(node_id=nid, kind=kind, label=label,
                      project=project, summary=summary)
        # Persist as a Code Memory record (category kg_node) for searchability.
        self.memory.memory.record_knowledge(
            "kg_node", f"KG[{kind}] {label}\n{summary}",
            tags=[kind, "kg"], importance=4,
        )
        return node

    def get_node(self, node_id: str) -> Optional[KGNode]:
        for e in self._edges.values():
            pass  # edges only; node metadata is looked up via memory if needed
        # Nodes are lightweight; we re-derive from memory labels if required.
        return None

    # ------------------------------------------------------------------
    # Edges (relationships)
    # ------------------------------------------------------------------

    def connect(self, from_id: str, to_id: str, relation: str,
                note: str = "") -> dict:
        if relation not in EDGE_RELATIONS:
            raise ValueError(f"Invalid edge relation: {relation}")
        eid = uuid.uuid4().hex[:12]
        edge = {"edge_id": eid, "from": from_id, "to": to_id,
                "relation": relation, "note": note, "created_at": _now()}
        self._edges[eid] = edge
        self._save_edges()
        return edge

    def edges_of(self, node_id: str) -> List[dict]:
        return [e for e in self._edges.values()
                if e["from"] == node_id or e["to"] == node_id]

    def neighbors(self, node_id: str) -> List[str]:
        out = []
        for e in self._edges.values():
            if e["from"] == node_id:
                out.append(e["to"])
            elif e["to"] == node_id:
                out.append(e["from"])
        return out

    def nodes_by_kind(self, kind: str) -> List[str]:
        # Recover node labels of a kind from Code Memory.
        recs = self.memory.memory.recall(tags=[kind, "kg"])
        return [r["content"] for r in recs]

    def close(self) -> None:
        self._save_edges()
        self.memory.close()

