"""Cold Storage DCAT Catalog (IF-COLD-CATALOG, FUN-COLD-005)."""
import json
import rdflib
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from ..domain.models import DcatDataset

router = APIRouter(prefix="/catalog")

_CATALOG_GRAPH = "urn:archpulse:graph:cold-catalog"
_DCAT_NS = "http://www.w3.org/ns/dcat#"
_PROV_NS = "http://www.w3.org/ns/prov#"
_BIR_NS = "https://arch-pulse.example/ns/bir#"


@router.post("/datasets", status_code=201)
async def register_dataset(request: Request) -> JSONResponse:
    body = await request.json()
    ds = DcatDataset.model_validate(body)

    repo = request.app.state.repo
    ntriples = _dataset_to_ntriples(ds)
    try:
        sparql = f"INSERT DATA {{\n    GRAPH <{_CATALOG_GRAPH}> {{\n{ntriples}    }}\n}}"
        await repo.sparql_update(sparql)
    except Exception as exc:
        raise HTTPException(409, f"Dataset registration failed: {exc}") from exc

    return JSONResponse({"datasetUri": ds.dataset_uri}, status_code=201)


@router.get("/datasets")
async def search_datasets(
    request: Request,
    tenant: str | None = None,
    dataClass: str | None = None,
    bir_id: str | None = None,
) -> JSONResponse:
    repo = request.app.state.repo

    filters: list[str] = []
    if tenant:
        filters.append(f"?ds <{_BIR_NS}tenantScope> {rdflib.Literal(tenant).n3()} .")
    if dataClass:
        filters.append(f"?ds <{_BIR_NS}dataClass> {rdflib.Literal(dataClass).n3()} .")
    if bir_id:
        # bir_id is a URI suffix — validate it rather than embedding raw
        try:
            import urllib.parse
            safe = urllib.parse.quote(bir_id, safe=":/-")
            filters.append(f"FILTER(CONTAINS(STR(?ds), {rdflib.Literal(safe).n3()}))")
        except Exception:
            raise HTTPException(400, "Invalid bir_id filter value")

    filter_block = "\n        ".join(filters)
    sparql = f"""
    PREFIX dcat: <{_DCAT_NS}>
    SELECT ?ds ?tenantScope ?dataClass ?optInJobId ?byteSize WHERE {{
        GRAPH <{_CATALOG_GRAPH}> {{
            ?ds a dcat:Dataset ;
                <{_BIR_NS}tenantScope>  ?tenantScope ;
                <{_BIR_NS}dataClass>   ?dataClass ;
                <{_BIR_NS}optInJobId>  ?optInJobId ;
                <{_DCAT_NS}byteSize>   ?byteSize .
            {filter_block}
        }}
    }}
    """
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)
    results = []
    for b in data.get("results", {}).get("bindings", []):
        results.append({
            "dataset_uri":   b["ds"]["value"],
            "tenant_scope":  b["tenantScope"]["value"],
            "data_class":    b["dataClass"]["value"],
            "opt_in_job_id": b["optInJobId"]["value"],
            "byte_size":     int(b["byteSize"]["value"]),
        })
    return JSONResponse(results)


def _dataset_to_ntriples(ds: DcatDataset) -> str:
    """Build N-Triples using rdflib so all literals are properly escaped."""
    g = rdflib.Graph()
    subj = rdflib.URIRef(ds.dataset_uri)
    g.add((subj, rdflib.RDF.type,                        rdflib.URIRef(f"{_DCAT_NS}Dataset")))
    g.add((subj, rdflib.URIRef(f"{_BIR_NS}tenantScope"), rdflib.Literal(ds.tenant_scope)))
    g.add((subj, rdflib.URIRef(f"{_BIR_NS}dataClass"),   rdflib.Literal(ds.data_class)))
    g.add((subj, rdflib.URIRef(f"{_BIR_NS}optInJobId"),  rdflib.Literal(ds.opt_in_job_id)))
    g.add((subj, rdflib.URIRef(f"{_DCAT_NS}byteSize"),   rdflib.Literal(ds.byte_size)))
    g.add((subj, rdflib.URIRef(f"{_PROV_NS}wasDerivedFrom"), rdflib.URIRef(ds.was_derived_from)))
    g.add((subj, rdflib.URIRef(f"{_DCAT_NS}startDate"),  rdflib.Literal(str(ds.period.start))))
    g.add((subj, rdflib.URIRef(f"{_DCAT_NS}endDate"),    rdflib.Literal(str(ds.period.end))))
    g.add((subj, rdflib.URIRef(f"{_BIR_NS}checksum"),    rdflib.Literal(ds.checksum.value)))
    return "".join(f"        {s.n3()} {p.n3()} {o.n3()} .\n" for s, p, o in g)
