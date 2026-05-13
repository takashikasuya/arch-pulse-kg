"""GraphRAG causal analysis service — FUN-ENERGY-002."""
from __future__ import annotations
import uuid

from ..domain.models import AnalysisRequest, AnalysisResult, CausalPath, Period
from ..domain.citation import (
    make_citation, build_assertion_citation_map, build_evidence_payload,
)
from ..ports.kg_reader import KgReader
from ..ports.ts_reader import TsReader

BIR_NS = "https://arch-pulse.example/ns/bir#"

_CONTEXT_QUERY = """
SELECT ?s ?p ?o WHERE {{
  {{ <{bir_id}> ?p ?o . BIND(<{bir_id}> AS ?s) }}
  UNION
  {{ ?s ?p <{bir_id}> . BIND(<{bir_id}> AS ?o) }}
}}
LIMIT 50
"""


async def run_causal_analysis(
    request: AnalysisRequest,
    kg: KgReader,
    ts: TsReader,
) -> AnalysisResult:
    job_id = str(uuid.uuid4())

    # 1. SPARQL path discovery
    query = _CONTEXT_QUERY.format(bir_id=request.context_bir_id)
    bindings = await kg.sparql_select(query)

    # 2. Build citation nodes from SPARQL results
    citations = []
    for row in bindings:
        s_val = row.get("s", {}).get("value", "")
        p_val = row.get("p", {}).get("value", "")
        o_val = row.get("o", {}).get("value", "")
        if not (s_val and p_val and o_val):
            continue
        cit = make_citation(
            bir_id=s_val,
            predicate=p_val,
            value=o_val,
            period=request.period,
            source="IF-KG-001",
        )
        citations.append(cit)

        # 3. If the object is a bir:point, also query TimescaleDB
        if o_val.startswith("urn:bir:point:"):
            ts_rows = await ts.query_telemetry(
                tenant_id=request.tenant_id,
                bir_point_id=o_val,
                start=request.period.start,
                end=request.period.end,
            )
            for row_ts in ts_rows:
                ts_cit = make_citation(
                    bir_id=o_val,
                    predicate="ts:measurement",
                    value=str(row_ts.get("value", "")),
                    period=Period(
                        start=row_ts.get("ts", request.period.start),
                        end=row_ts.get("ts", request.period.end),
                    ),
                    source="IF-INFRA-002",
                )
                citations.append(ts_cit)

    # 4. Assemble causal paths — one path per SPARQL triple
    paths: list[CausalPath] = []
    for i, (row, cit) in enumerate(zip(bindings, citations[: len(bindings)])):
        s_val = row.get("s", {}).get("value", "")
        o_val = row.get("o", {}).get("value", "")
        p_val = row.get("p", {}).get("value", "")
        path = CausalPath(
            path_id=str(uuid.uuid4()),
            nodes=[s_val, o_val],
            predicates=[p_val],
            citation_ids=[cit.citation_id],
        )
        paths.append(path)

    # 5. TC-INT-022: build 1:1 assertion→citation map
    acm = build_assertion_citation_map(paths, citations)

    # 6. Evidence payload for LLM
    payload = build_evidence_payload(request.question, paths, citations, acm)

    return AnalysisResult(
        job_id=job_id,
        tenant_id=request.tenant_id,
        context_bir_id=request.context_bir_id,
        period=request.period,
        causal_paths=paths,
        citations=citations,
        assertion_citation_map=acm,
        evidence_payload=payload,
    )
