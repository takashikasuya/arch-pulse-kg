"""Cold Storage DCAT Catalog (IF-COLD-CATALOG, FUN-COLD-005)."""
import json
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
    turtle = _dataset_to_turtle(ds)
    try:
        sparql = f"""
        INSERT DATA {{
            GRAPH <{_CATALOG_GRAPH}> {{
                {turtle}
            }}
        }}
        """
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
        filters.append(f'?ds <{_BIR_NS}tenantScope> "{tenant}" .')
    if dataClass:
        filters.append(f'?ds <{_BIR_NS}dataClass> "{dataClass}" .')
    if bir_id:
        filters.append(f'FILTER(CONTAINS(STR(?ds), "{bir_id}"))')

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


def _dataset_to_turtle(ds: DcatDataset) -> str:
    lines = [
        f'<{ds.dataset_uri}> a <{_DCAT_NS}Dataset> ;',
        f'    <{_BIR_NS}tenantScope>  "{ds.tenant_scope}" ;',
        f'    <{_BIR_NS}dataClass>    "{ds.data_class}" ;',
        f'    <{_BIR_NS}optInJobId>   "{ds.opt_in_job_id}" ;',
        f'    <{_DCAT_NS}byteSize>    {ds.byte_size} ;',
        f'    <{_PROV_NS}wasDerivedFrom> <{ds.was_derived_from}> ;',
        f'    <{_DCAT_NS}startDate>   "{ds.period.start}" ;',
        f'    <{_DCAT_NS}endDate>     "{ds.period.end}" ;',
        f'    <{_BIR_NS}checksum>     "{ds.checksum.value}" .',
    ]
    return "\n        ".join(lines)
