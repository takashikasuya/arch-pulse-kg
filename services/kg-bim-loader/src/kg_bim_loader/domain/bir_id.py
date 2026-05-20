"""bir_id generation following ADR-006 (urn:bir:{kind}:{uuid})."""
from __future__ import annotations
import re
import uuid

_BIR_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID v5 namespace

_IFC22_PAD = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$"


def _ifc_guid_to_hex(ifc_guid: str) -> str:
    """Convert 22-char IFC base64 GUID to standard hex UUID string."""
    if re.fullmatch(r"[0-9a-fA-F-]{32,36}", ifc_guid.replace("-", "")):
        return ifc_guid
    # IFC 22-char base64 encoding
    n = 0
    for char in ifc_guid:
        n = n * 64 + _IFC22_PAD.index(char)
    return format(n, "032x")


def from_ifc_guid(ifc_guid: str, kind: str) -> str:
    """Generate a deterministic bir_id from an IFC GUID via UUID v5 (ADR-006)."""
    hex_str = _ifc_guid_to_hex(ifc_guid)
    uid = uuid.uuid5(_BIR_NS, hex_str)
    return f"urn:bir:{kind}:{uid}"


def new(kind: str) -> str:
    """Generate a new random bir_id (UUID v4)."""
    return f"urn:bir:{kind}:{uuid.uuid4()}"
