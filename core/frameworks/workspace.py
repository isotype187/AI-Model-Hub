"""Nexus98 WWW — Workspace Reality Continuity framework.

Gives Nexus98 an accurate, persistent model of *workspace reality*: the active
projects, the files and system state they touch, and the relationships between
components. It is the internal "World Workspace Web" — a graph of what exists,
how parts relate, and how to recover context after an interruption.

Design:
  * Built on top of the existing :mod:`core.continuity` store (JSON) and
    :mod:`core.code_memory` (SQLite). It does NOT replace either; it uses them
    as storage backends and adds structured project/file/relationship records.
  * The Project Engine remains the only authorized file mutator; this framework
    only *records* and *queries* reality, never writes source files itself.
  * Fully additive. Performs no autonomy-state mutation.

Storage:
  * ``data/workspace.json`` holds projects, files, components, and edges.
  * Recovery/continuity notes delegate to :class:`core.continuity.WorkspaceContinuity`.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "workspace.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ComponentRef:
    """A node in the workspace web (file, module, service, config)."""

    id: str
    kind: str  # file | module | service | config | agent | ui
    path: str
    project: str = "nexus98"
    summary: str = ""
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "path": self.path,
            "project": self.project, "summary": self.summary,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ComponentRef":
        return cls(
            id=d["id"], kind=d["kind"], path=d["path"],
            project=d.get("project", "nexus98"),
            summary=d.get("summary", ""), updated_at=d.get("updated_at", _now()),
        )


class WorkspaceReality:
    """The Workspace Reality store: projects, files, components, and edges."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, dict] = self._load()

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, dict]:
        if not self.path.exists():
            return self._empty()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in ("projects", "components", "edges", "system_state"):
                data.setdefault(key, {} if key != "edges" else [])
            return data
        except (json.JSONDecodeError, OSError):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                shutil.copy2(self.path, self.path.with_suffix(f".corrupt_{ts}.json"))
            except OSError:
                pass
            return self._empty()

    def _empty(self) -> Dict[str, dict]:
        return {
            "version": 1,
            "updated_at": _now(),
            "projects": {},      # project_id -> project record
            "components": {},    # component_id -> ComponentRef dict
            "edges": [],         # list of {from,to,relation,....}
            "system_state": {},  # key/value runtime facts
        }

    def save(self) -> None:
        self._data["updated_at"] = _now()
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def register_project(
        self, name: str, *, description: str = "", status: str = "active",
        owner: str = "agent",
    ) -> str:
        pid = uuid.uuid4().hex[:12]
        self._data["projects"][pid] = {
            "project_id": pid, "name": name, "description": description,
            "status": status, "owner": owner, "created_at": _now(),
            "updated_at": _now(),
        }
        self.save()
        return pid

    def update_project(self, project_id: str, **fields) -> bool:
        proj = self._data["projects"].get(project_id)
        if not proj:
            return False
        proj.update(fields)
        proj["updated_at"] = _now()
        self.save()
        return True

    def get_project(self, project_id: str) -> Optional[dict]:
        return self._data["projects"].get(project_id)

    def list_projects(self, status: Optional[str] = None) -> List[dict]:
        projs = list(self._data["projects"].values())
        if status:
            projs = [p for p in projs if p.get("status") == status]
        return projs

    # ------------------------------------------------------------------
    # Components / files
    # ------------------------------------------------------------------

    def register_component(
        self, path: str, kind: str, *, project: str = "nexus98",
        summary: str = "",
    ) -> str:
        cid = uuid.uuid5(uuid.NAMESPACE_URL, f"comp:{path}").hex[:12]
        comp = ComponentRef(id=cid, kind=kind, path=path, project=project, summary=summary)
        self._data["components"][cid] = comp.to_dict()
        self.save()
        return cid

    def get_component(self, component_id: str) -> Optional[dict]:
        return self._data["components"].get(component_id)

    def find_component_by_path(self, path: str) -> Optional[dict]:
        for c in self._data["components"].values():
            if c["path"] == path:
                return c
        return None

    # ------------------------------------------------------------------
    # Relationships (the "web")
    # ------------------------------------------------------------------

    def link(self, from_id: str, to_id: str, relation: str,
             *, detail: str = "") -> dict:
        edge = {
            "edge_id": uuid.uuid4().hex[:12],
            "from": from_id, "to": to_id, "relation": relation,
            "detail": detail, "created_at": _now(),
        }
        self._data["edges"].append(edge)
        self.save()
        return edge

    def relations_of(self, component_id: str) -> List[dict]:
        return [
            e for e in self._data["edges"]
            if e["from"] == component_id or e["to"] == component_id
        ]

    def neighbors(self, component_id: str) -> List[str]:
        out = []
        for e in self._data["edges"]:
            if e["from"] == component_id:
                out.append(e["to"])
            elif e["to"] == component_id:
                out.append(e["from"])
        return out

    # ------------------------------------------------------------------
    # System state
    # ------------------------------------------------------------------

    def set_state(self, key: str, value) -> None:
        self._data["system_state"][key] = value
        self.save()

    def get_state(self, key: str = None):
        if key is None:
            return dict(self._data["system_state"])
        return self._data["system_state"].get(key)

    # ------------------------------------------------------------------
    # Recovery summary
    # ------------------------------------------------------------------

    def reality_snapshot(self) -> dict:
        """A concise view of workspace reality for recovery/continuity."""
        return {
            "updated_at": self._data.get("updated_at"),
            "projects": len(self._data["projects"]),
            "active_projects": [
                p["name"] for p in self._data["projects"].values()
                if p.get("status") == "active"
            ],
            "components": len(self._data["components"]),
            "relationships": len(self._data["edges"]),
            "system_state_keys": list(self._data["system_state"].keys()),
        }

    def close(self) -> None:
        self.save()
