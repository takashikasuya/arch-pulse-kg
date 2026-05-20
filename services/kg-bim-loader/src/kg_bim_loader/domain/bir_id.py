"""bir_id generation following ADR-006 (urn:bir:{kind}:{uuid}).

Namespace and uuid5 derivation are aligned with CS-KG-STORE's canonical implementation
(services/kg-store/src/kg_store/domain/bir_id.py) to ensure stable bir_ids across services.
"""
from __future__ import annotations
import uuid

# Must match NS_BIR_IFC in CS-KG-STORE (ADR-006)
NS_BIR_IFC = uuid.UUID("6f29e3c8-3a13-4d20-a43e-1fc1bf6d98e1")


def from_ifc_guid(ifc_guid: str, kind: str) -> str:
    """Generate a deterministic bir_id from an IFC GlobalId string via UUID v5 (ADR-006)."""
    uid = uuid.uuid5(NS_BIR_IFC, ifc_guid)
    return f"urn:bir:{kind}:{uid}"


def new(kind: str) -> str:
    """Generate a new random bir_id (UUID v4)."""
    return f"urn:bir:{kind}:{uuid.uuid4()}"
