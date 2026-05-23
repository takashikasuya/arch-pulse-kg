"""Dataspace DCAT catalog endpoint (IF-CLOUD-DSC-DCAT, REQ-SOS-056).

Only accessible via gRPC reverse tunnel (x-tunnel-source: cloud-dsc header).
Direct external access returns 403 to enforce ADR-017/ADR-026.
"""
from __future__ import annotations
import json
import logging
import rdflib
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dataspace")

_CATALOG_GRAPH = "urn:archpulse:graph:cold-catalog"
_DCAT_NS = "http://www.w3.org/ns/dcat#"
_DCT_NS = "http://purl.org/dc/terms/"
_BIR_NS = "https://arch-pulse.example/ns/bir#"
_XSD_BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"


def _require_tunnel(request: Request) -> None:
    if request.headers.get("x-tunnel-source") != "cloud-dsc":
        raise HTTPException(403, "Direct access not allowed; use tunnel relay")


def _verify_jwt(authorization: str = Header(default="")) -> dict:
    secret = settings.tunnel_jwt_secret
    if not secret:
        raise HTTPException(503, "JWT secret not configured")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        logger.debug("JWT validation failed: %s", exc)
        raise HTTPException(401, "Invalid token") from exc


@router.get("/catalog")
async def get_dataspace_catalog(
    request: Request,
    _tunnel: None = Depends(_require_tunnel),
    claims: dict = Depends(_verify_jwt),
) -> Response:
    """Return only datasets flagged as exposed, filtered to the JWT's tenant_id."""
    repo = request.app.state.repo
    accept = request.headers.get("accept", "application/ld+json")

    tenant_id = claims.get("tenant_id", "")
    tenant_filter = ""
    if tenant_id:
        tenant_filter = f'FILTER(?tenantScope = {rdflib.Literal(tenant_id).n3()})'

    sparql = f"""
    PREFIX dcat: <{_DCAT_NS}>
    SELECT ?ds ?tenantScope ?dataClass ?byteSize ?license ?dist ?accessURL ?mediaType WHERE {{
        GRAPH <{_CATALOG_GRAPH}> {{
            ?ds a dcat:Dataset ;
                <{_BIR_NS}datasetExposed> "true"^^<{_XSD_BOOLEAN}> ;
                <{_BIR_NS}tenantScope>    ?tenantScope ;
                <{_BIR_NS}dataClass>      ?dataClass ;
                <{_DCAT_NS}byteSize>      ?byteSize .
            OPTIONAL {{ ?ds <{_DCT_NS}license> ?license }}
            OPTIONAL {{
                ?ds <{_DCAT_NS}distribution> ?dist .
                OPTIONAL {{ ?dist <{_DCAT_NS}accessURL> ?accessURL }}
                OPTIONAL {{ ?dist <{_DCAT_NS}mediaType> ?mediaType }}
            }}
            {tenant_filter}
        }}
    }}
    """
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)

    g = rdflib.Graph()
    g.bind("dcat", rdflib.Namespace(_DCAT_NS))
    g.bind("dct", rdflib.Namespace(_DCT_NS))
    g.bind("bir", rdflib.Namespace(_BIR_NS))

    for b in data.get("results", {}).get("bindings", []):
        subj = rdflib.URIRef(b["ds"]["value"])
        g.add((subj, rdflib.RDF.type, rdflib.URIRef(f"{_DCAT_NS}Dataset")))
        g.add((subj, rdflib.URIRef(f"{_BIR_NS}tenantScope"), rdflib.Literal(b["tenantScope"]["value"])))
        g.add((subj, rdflib.URIRef(f"{_BIR_NS}dataClass"), rdflib.Literal(b["dataClass"]["value"])))
        g.add((subj, rdflib.URIRef(f"{_DCAT_NS}byteSize"), rdflib.Literal(int(b["byteSize"]["value"]))))
        if "license" in b:
            g.add((subj, rdflib.URIRef(f"{_DCT_NS}license"), rdflib.URIRef(b["license"]["value"])))
        if "dist" in b:
            d = b["dist"]
            dist_ref = rdflib.BNode(d["value"]) if d["type"] == "bnode" else rdflib.URIRef(d["value"])
            g.add((subj, rdflib.URIRef(f"{_DCAT_NS}distribution"), dist_ref))
            g.add((dist_ref, rdflib.RDF.type, rdflib.URIRef(f"{_DCAT_NS}Distribution")))
            if "accessURL" in b:
                g.add((dist_ref, rdflib.URIRef(f"{_DCAT_NS}accessURL"), rdflib.URIRef(b["accessURL"]["value"])))
            if "mediaType" in b:
                g.add((dist_ref, rdflib.URIRef(f"{_DCAT_NS}mediaType"), rdflib.Literal(b["mediaType"]["value"])))

    if "text/turtle" in accept:
        return Response(g.serialize(format="turtle"), media_type="text/turtle")
    return Response(g.serialize(format="json-ld"), media_type="application/ld+json")
