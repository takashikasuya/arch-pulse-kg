"""Domain models for GraphRAG causal analysis (REQ-SOS-022)."""
from __future__ import annotations
from pydantic import BaseModel, Field


class Period(BaseModel):
    start: str  # ISO 8601 datetime
    end: str


class CitationNode(BaseModel):
    """Machine-readable citation attached to each causal assertion (REQ-SOS-022)."""
    citation_id: str
    bir_id: str       # urn:bir:... entity being cited
    predicate: str    # RDF predicate used to discover this node
    value: str        # object value (IRI or literal)
    period: Period
    model_version: str = "1.0"
    source: str       # "IF-KG-001" | "IF-INFRA-002"


class CausalPath(BaseModel):
    """A chain of RDF nodes representing a potential causal relationship."""
    path_id: str
    nodes: list[str]       # bir_id list (subject … object)
    predicates: list[str]  # predicate per hop
    citation_ids: list[str]


class AnalysisRequest(BaseModel):
    tenant_id: str
    context_bir_id: str
    period: Period
    question: str


class AnalysisResult(BaseModel):
    job_id: str
    tenant_id: str
    context_bir_id: str
    period: Period
    causal_paths: list[CausalPath]
    citations: list[CitationNode]
    assertion_citation_map: dict[str, str] = Field(default_factory=dict)
    evidence_payload: dict = Field(default_factory=dict)
