"""Citation metadata builder (REQ-SOS-022)."""
from __future__ import annotations
import uuid
from .models import CitationNode, CausalPath, Period


def make_citation(bir_id: str, predicate: str, value: str,
                  period: Period, source: str = "IF-KG-001") -> CitationNode:
    return CitationNode(
        citation_id=str(uuid.uuid4()),
        bir_id=bir_id,
        predicate=predicate,
        value=value,
        period=period,
        source=source,
    )


def build_assertion_citation_map(
    paths: list[CausalPath],
    citations: list[CitationNode],
) -> dict[str, str]:
    """Return 1:1 assertion→citation mapping required by TC-INT-022.

    Each citation_id appears at most once; this ensures zero uncited claims.
    """
    citation_by_id = {c.citation_id: c for c in citations}
    mapping: dict[str, str] = {}
    for path in paths:
        for cid in path.citation_ids:
            if cid in citation_by_id and cid not in mapping.values():
                assertion_key = f"{path.path_id}:{cid}"
                mapping[assertion_key] = cid
    return mapping


def build_evidence_payload(
    question: str,
    paths: list[CausalPath],
    citations: list[CitationNode],
    assertion_citation_map: dict[str, str],
) -> dict:
    """Structured payload passed to LLM to suppress hallucination."""
    return {
        "question": question,
        "causal_paths": [p.model_dump() for p in paths],
        "citations": [c.model_dump() for c in citations],
        "assertion_citation_map": assertion_citation_map,
        "instruction": (
            "Answer only using the provided causal_paths and citations. "
            "Every claim must reference a citation_id from the citations list."
        ),
    }
