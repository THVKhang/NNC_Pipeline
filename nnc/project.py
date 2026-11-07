"""Design workspace layout, gate state and baseline hashes.

A design workspace is one folder per IP:

    designs/<ip>/
        spec/            specification and standards/ (inputs)
        rtl/             the DUT; never copied into the sandbox of a generator agent
        work/            artifacts of the flow (rules.json, contract.json, agent logs, ...)
        verif/           generated verification sources (sva/, tests/)
        nnc_state.json   gate approvals with the hashes of the artifacts they approved

A gate approval records the SHA-256 of every artifact it covers. When an artifact changes later,
the gate becomes STALE and every later gate becomes BLOCKED, so evidence from an old baseline is
never reused silently (principle PR-5 of docs/ARCHITECTURE.md).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = "nnc_state.json"
STATE_VERSION = 1

# Gate order matters: each gate requires every earlier gate to be APPROVED.
GATES: tuple[str, ...] = ("G1_rules", "G2_contract", "G3_verif_sources", "G4_signoff")

# Artifacts (paths relative to the design root; a folder is hashed as a whole) covered by each gate.
GATE_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "G1_rules": ("work/rules.json",),
    "G2_contract": ("work/contract.json",),
    "G3_verif_sources": ("verif",),
    "G4_signoff": ("work/results.json",),
}

LAYOUT_DIRS: tuple[str, ...] = (
    "spec/standards",
    "rtl",
    "work",
    "verif/sva",
    "verif/tests",
)

# Folders whose content must never reach a verification-generator agent (principle PR-1).
DUT_DIRS: tuple[str, ...] = ("rtl",)

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]*$")


class ProjectError(Exception):
    """A user-facing error about the design workspace or a gate."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_path(path: Path) -> str | None:
    """SHA-256 of a file, or of a folder (sorted relative paths and contents); None if missing.

    An empty folder hashes like a missing one: it holds no artifact to approve.
    """
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
        if not files:
            return None
        h = hashlib.sha256()
        for f in files:
            h.update(f.relative_to(path).as_posix().encode("utf-8"))
            h.update(b"\0")
            h.update(hashlib.sha256(f.read_bytes()).digest())
        return h.hexdigest()
    return None


@dataclass(frozen=True)
class GateStatus:
    gate: str
    state: str  # APPROVED | STALE | BLOCKED | PENDING
    detail: str


class Design:
    """One design workspace."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    # ----------------------------------------------------------------- creation / loading
    @classmethod
    def init(cls, root: Path) -> "Design":
        root = Path(root)
        if not _NAME_RE.match(root.name):
            raise ProjectError(
                f"invalid design name '{root.name}': use letters, digits, '_' or '-', starting with a letter"
            )
        if (root / STATE_FILE).exists():
            raise ProjectError(f"{root} is already a design workspace")
        for d in LAYOUT_DIRS:
            (root / d).mkdir(parents=True, exist_ok=True)
        design = cls(root)
        design._write_state({"version": STATE_VERSION, "design": root.name, "created": _now(), "gates": {}})
        return design

    @classmethod
    def open(cls, root: Path) -> "Design":
        design = cls(root)
        if not design.state_path.exists():
            raise ProjectError(f"{design.root} is not a design workspace (no {STATE_FILE}); run 'nnc init' first")
        return design

    # ----------------------------------------------------------------- state
    @property
    def state_path(self) -> Path:
        return self.root / STATE_FILE

    @property
    def name(self) -> str:
        return self.root.name

    def dut_dirs(self) -> list[Path]:
        return [self.root / d for d in DUT_DIRS]

    def _read_state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ProjectError(f"{self.state_path} is not valid JSON: {e}") from e

    def _write_state(self, state: dict) -> None:
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    # ----------------------------------------------------------------- configuration
    @property
    def work(self) -> Path:
        return self.root / "work"

    def config(self) -> dict:
        """Design configuration: top module, documents (role, tag, section filters), clock/reset."""
        return self._read_state().get("config", {})

    def set_config(self, **values) -> dict:
        state = self._read_state()
        cfg = state.setdefault("config", {})
        for k, v in values.items():
            if v is None:
                cfg.pop(k, None)
            else:
                cfg[k] = v
        self._write_state(state)
        return cfg

    def add_document(self, file: str, role: str, tag: str, sections: list[str] | None = None,
                     skip: list[str] | None = None) -> dict:
        """Register a document: role 'ip_spec' (the DUT's own specification) or 'standard'."""
        if role not in ("ip_spec", "standard"):
            raise ProjectError("role must be 'ip_spec' or 'standard'")
        if not re.match(r"^[A-Z][A-Z0-9]{0,7}$", tag):
            raise ProjectError("tag must be 1-8 capital letters/digits, starting with a letter (e.g. BR, TL)")
        state = self._read_state()
        docs = state.setdefault("config", {}).setdefault("documents", [])
        docs[:] = [d for d in docs if d["file"] != file]
        if any(d["tag"] == tag for d in docs):
            raise ProjectError(f"tag {tag} is already used by another document")
        if role == "ip_spec" and any(d["role"] == "ip_spec" for d in docs):
            raise ProjectError("the design already has an ip_spec document")
        entry = {"file": file, "role": role, "tag": tag, "sections": sections or [], "skip": skip or []}
        docs.append(entry)
        self._write_state(state)
        return entry

    def documents(self) -> list[dict]:
        return self.config().get("documents", [])

    def gate_approved(self, gate: str) -> bool:
        return next(s for s in self.status() if s.gate == gate).state == "APPROVED"

    def require_gate(self, gate: str, unreviewed: bool) -> list[str]:
        """Raise unless the gate is approved; with unreviewed=True return the gates being bypassed.

        Every artifact produced past a bypassed gate carries the list, and the report marks it, so
        an unreviewed run can never pass for a reviewed one (principle PR-5)."""
        missing = []
        for st in self.status():
            if st.state != "APPROVED":
                missing.append(st.gate)
            if st.gate == gate:
                break
        if missing and not unreviewed:
            raise ProjectError(f"{gate} is not approved ({', '.join(missing)} open); review and run "
                               f"'nnc gate approve', or pass --unreviewed for an exploratory run")
        return missing

    def artifact_hashes(self, gate: str) -> dict[str, str | None]:
        return {rel: hash_path(self.root / rel) for rel in GATE_ARTIFACTS[gate]}

    # ----------------------------------------------------------------- gates
    def status(self) -> list[GateStatus]:
        gates = self._read_state().get("gates", {})
        out: list[GateStatus] = []
        upstream_ok = True
        for gate in GATES:
            rec = gates.get(gate)
            current = self.artifact_hashes(gate)
            if not upstream_ok:
                state, detail = "BLOCKED", "an earlier gate is not approved or is stale"
            elif rec is None:
                missing = [k for k, v in current.items() if v is None]
                detail = f"missing: {', '.join(missing)}" if missing else "artifacts ready for review"
                state = "PENDING"
            else:
                changed = [k for k, v in current.items() if rec["hashes"].get(k) != v]
                if changed:
                    state, detail = "STALE", f"changed since approval: {', '.join(changed)}"
                else:
                    state, detail = "APPROVED", f"by {rec['by']} at {rec['at']}"
            out.append(GateStatus(gate, state, detail))
            upstream_ok = upstream_ok and state == "APPROVED"
        return out

    def approve(self, gate: str, by: str, note: str = "") -> GateStatus:
        if gate not in GATES:
            raise ProjectError(f"unknown gate '{gate}'; gates are: {', '.join(GATES)}")
        if not by.strip():
            raise ProjectError("an approval needs the reviewer's name (--by)")
        for st in self.status():
            if st.gate == gate:
                break
            if st.state != "APPROVED":
                raise ProjectError(f"cannot approve {gate}: {st.gate} is {st.state} ({st.detail})")
        hashes = self.artifact_hashes(gate)
        missing = [k for k, v in hashes.items() if v is None]
        if missing:
            raise ProjectError(f"cannot approve {gate}: missing artifacts: {', '.join(missing)}")
        state = self._read_state()
        state.setdefault("gates", {})[gate] = {"by": by.strip(), "at": _now(), "note": note, "hashes": hashes}
        self._write_state(state)
        return next(s for s in self.status() if s.gate == gate)

    def revoke(self, gate: str) -> None:
        if gate not in GATES:
            raise ProjectError(f"unknown gate '{gate}'; gates are: {', '.join(GATES)}")
        state = self._read_state()
        if state.get("gates", {}).pop(gate, None) is None:
            raise ProjectError(f"{gate} has no approval to revoke")
        self._write_state(state)
