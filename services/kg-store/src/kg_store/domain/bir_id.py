import re
import uuid
from typing import NamedTuple

BIR_KINDS: frozenset[str] = frozenset({
    "building", "floor", "space", "zone", "surface", "opening",
    "device", "point", "system", "geometry", "schedule", "tenant",
    "policy", "dataset", "model", "run", "visitor", "robot", "ctrl-seq",
})

_PATTERN = re.compile(
    r"^urn:bir:(?P<kind>[a-z][a-z\-]*):(?P<uuid>"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
)

# Namespace UUID for IFC GlobalId → bir_id (v5) derivation (ADR-006)
NS_BIR_IFC = uuid.UUID("6f29e3c8-3a13-4d20-a43e-1fc1bf6d98e1")


class BirId(NamedTuple):
    kind: str
    uid: uuid.UUID
    raw: str


def parse(urn: str) -> BirId:
    m = _PATTERN.match(urn)
    if not m:
        raise ValueError(f"Invalid bir_id format: {urn!r}")
    kind = m["kind"]
    if kind not in BIR_KINDS:
        raise ValueError(f"Unknown bir_id kind: {kind!r}")
    return BirId(kind=kind, uid=uuid.UUID(m["uuid"]), raw=urn)


def from_ifc_guid(kind: str, ifc_guid: str) -> BirId:
    if kind not in BIR_KINDS:
        raise ValueError(f"Unknown bir_id kind: {kind!r}")
    uid = uuid.uuid5(NS_BIR_IFC, ifc_guid)
    raw = f"urn:bir:{kind}:{uid}"
    return BirId(kind=kind, uid=uid, raw=raw)


def new(kind: str) -> BirId:
    if kind not in BIR_KINDS:
        raise ValueError(f"Unknown bir_id kind: {kind!r}")
    uid = uuid.uuid4()
    raw = f"urn:bir:{kind}:{uid}"
    return BirId(kind=kind, uid=uid, raw=raw)


def to_nats_slug(urn: str) -> str:
    """Replace ':' with '-' for use in NATS subject tokens."""
    return urn.replace(":", "-")
