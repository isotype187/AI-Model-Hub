"""Nexus98 Extension / Plugin framework.

Foundation for future expansion. It manages *pluggable components* (extensions)
with metadata and a lifecycle, distinct from the Tool Registry which catalogs
*tool capabilities* of already-existing functions.

Responsibilities:
  * Register an extension with id, name, version, author, capabilities, hooks.
  * Discover registered extensions.
  * Lifecycle management: registered -> enabled -> active, and back down.
  * Store extension metadata + state in ``data/extensions.json``.

It performs NO code execution of extension bodies and makes NO autonomy-state
changes. Extensions are descriptive records; Nexus98 may consult them to know
what optional capabilities exist. This deliberately does not duplicate the
Tool Registry's function-level capability map.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "extensions.json"

# Lifecycle states (ordered).
LIFECYCLE = ("registered", "enabled", "active", "disabled", "error")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Extension:
    """A registered, optionally activatable component."""

    ext_id: str
    name: str
    version: str
    author: str = "unknown"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)  # e.g. "on_startup"
    state: str = "registered"
    metadata: Dict[str, str] = field(default_factory=dict)
    registered_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "ext_id": self.ext_id, "name": self.name, "version": self.version,
            "author": self.author, "description": self.description,
            "capabilities": list(self.capabilities), "hooks": list(self.hooks),
            "state": self.state, "metadata": dict(self.metadata),
            "registered_at": self.registered_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Extension":
        return cls(
            ext_id=d["ext_id"], name=d["name"], version=d["version"],
            author=d.get("author", "unknown"), description=d.get("description", ""),
            capabilities=list(d.get("capabilities", [])),
            hooks=list(d.get("hooks", [])),
            state=d.get("state", "registered"),
            metadata=dict(d.get("metadata", {})),
            registered_at=d.get("registered_at", _now()),
            updated_at=d.get("updated_at", _now()),
        )


class ExtensionRegistry:
    """Registers and tracks extensions with lifecycle management."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ext: Dict[str, Extension] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Extension]:
        if not self.path.exists():
            return {}
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            return {rid: Extension.from_dict(r) for rid, r in rows.items()}
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            return {}

    def save(self) -> None:
        payload = {rid: e.to_dict() for rid, e in self._ext.items()}
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        import shutil
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Register / discover
    # ------------------------------------------------------------------

    def register(self, name: str, version: str, *, author: str = "unknown",
                 description: str = "", capabilities: Optional[List[str]] = None,
                 hooks: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, str]] = None) -> Extension:
        ext_id = uuid.uuid5(uuid.NAMESPACE_URL, f"ext:{name}:{version}").hex[:12]
        if ext_id in self._ext:
            return self._ext[ext_id]
        ext = Extension(
            ext_id=ext_id, name=name, version=version, author=author,
            description=description, capabilities=list(capabilities or []),
            hooks=list(hooks or []), state="registered",
            metadata=dict(metadata or {}),
        )
        self._ext[ext_id] = ext
        self.save()
        return ext

    def get(self, ext_id: str) -> Optional[Extension]:
        return self._ext.get(ext_id)

    def list_extensions(self, state: Optional[str] = None) -> List[Extension]:
        exts = list(self._ext.values())
        if state:
            exts = [e for e in exts if e.state == state]
        return exts

    def discover(self, capability: Optional[str] = None,
                 hook: Optional[str] = None) -> List[Extension]:
        out = list(self._ext.values())
        if capability:
            out = [e for e in out if capability in e.capabilities]
        if hook:
            out = [e for e in out if hook in e.hooks]
        return out

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def set_state(self, ext_id: str, state: str) -> bool:
        if state not in LIFECYCLE:
            raise ValueError(f"Invalid lifecycle state: {state}")
        ext = self._ext.get(ext_id)
        if not ext:
            return False
        ext.state = state
        ext.updated_at = _now()
        self.save()
        return True

    def enable(self, ext_id: str) -> bool:
        return self.set_state(ext_id, "enabled")

    def activate(self, ext_id: str) -> bool:
        # Can only activate something that is enabled.
        ext = self._ext.get(ext_id)
        if not ext or ext.state not in ("enabled", "active"):
            return False
        return self.set_state(ext_id, "active")

    def disable(self, ext_id: str) -> bool:
        return self.set_state(ext_id, "disabled")

    def capability_summary(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for e in self._ext.values():
            for cap in e.capabilities:
                out.setdefault(cap, []).append(e.name)
        return out

    def close(self) -> None:
        self.save()
