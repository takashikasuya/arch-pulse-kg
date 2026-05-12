"""SHACL validation endpoint (IF-KG-001 /shacl/validate)."""
import io
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response

router = APIRouter()


@router.post("/shacl/validate")
async def shacl_validate(request: Request) -> Response:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", "text/turtle")
    shapes_ttl: str = request.app.state.bir_shapes_ttl

    if "multipart/form-data" in content_type:
        form = await request.form()
        data_str = form.get("data", "")
        custom_shapes = form.get("shapes", None)
    elif "application/json" in content_type:
        body = await request.json()
        data_str = body.get("data", "")
        custom_shapes = body.get("shapes", None)
    else:
        body_bytes = await request.body()
        data_str = body_bytes.decode()
        custom_shapes = None

    if not data_str:
        raise HTTPException(400, "Missing 'data' graph")

    shapes_src = custom_shapes if custom_shapes else shapes_ttl
    conforms, report_graph, _report_text = _run_shacl(data_str, shapes_src)
    buf = io.BytesIO()
    report_graph.serialize(buf, format="turtle")
    report_turtle = buf.getvalue().decode()

    if "application/ld+json" in accept:
        buf2 = io.BytesIO()
        report_graph.serialize(buf2, format="json-ld")
        return Response(content=buf2.getvalue(), media_type="application/ld+json")
    return Response(content=report_turtle.encode(), media_type="text/turtle")


def _run_shacl(data_ttl: str, shapes_ttl: str):
    from pyshacl import validate  # type: ignore[import]

    return validate(
        data_graph=data_ttl,
        shacl_graph=shapes_ttl,
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="none",
    )
