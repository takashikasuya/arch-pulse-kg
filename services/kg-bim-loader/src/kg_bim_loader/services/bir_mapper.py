"""BIR mapping service — converts IfcEntity to BIR Turtle using SBCO/REC/Brick ontology."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import importlib.resources
import yaml

from ..domain.bir_id import from_ifc_guid
from ..domain.ifc_model import IfcEntity

_BIR_NS = "https://arch-pulse.example/ns/bir#"
_REC_NS = "https://w3id.org/rec/"
_BRICK_NS = "https://brickschema.org/schema/Brick#"

_NS_MAP = {
    "rec:": _REC_NS,
    "brick:": _BRICK_NS,
    "bir:": _BIR_NS,
    "xsd:": "http://www.w3.org/2001/XMLSchema#",
}


@lru_cache(maxsize=1)
def _load_haystack_map() -> dict:
    pkg = importlib.resources.files("kg_bim_loader.taxonomies")
    return yaml.safe_load(pkg.joinpath("ifc-haystack-map.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_property_map() -> list[dict]:
    pkg = importlib.resources.files("kg_bim_loader.taxonomies")
    data = yaml.safe_load(pkg.joinpath("ifc-property-map.yaml").read_text(encoding="utf-8"))
    return data.get("mappings", [])


def _xsd_literal(value: str, datatype_prefixed: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"^^{datatype_prefixed}'


class BirMappingService:
    def to_turtle(self, entity: IfcEntity, tenant_id: str) -> str:
        haystack_map = _load_haystack_map()
        mappings = haystack_map.get("mappings", {})
        entry = mappings.get(entity.ifc_class, {})

        kind = entry.get("kind", "device")
        rdf_types = entry.get("rdf_types", [])
        tags = entry.get("tags", [])

        bir_id = from_ifc_guid(entity.ifc_guid, kind)

        lines: list[str] = [
            f"@prefix bir:   <{_BIR_NS}> .",
            f"@prefix rec:   <{_REC_NS}> .",
            f"@prefix brick: <{_BRICK_NS}> .",
            "@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .",
            "",
        ]

        # rdf:type assertions — use prefixed names (prefixes declared above)
        type_names = ["bir:Entity"] + list(rdf_types)
        type_str = ", ".join(type_names)

        triples: list[str] = [f"a {type_str}"]
        triples.append('bir:status "Active"^^xsd:string')
        triples.append(f"bir:tenantScope <{tenant_id}>")
        triples.append(f'bir:hasIfcGuid "{entity.ifc_guid}"^^xsd:string')

        for tag in tags:
            triples.append(f'bir:customTag "{tag}"^^xsd:string')

        # Pset property mapping — use prefixed predicate names
        pset_map = _load_property_map()
        for rule in pset_map:
            pset_name = rule["pset"]
            prop_name = rule["prop"]
            pset_data = entity.pset_values.get(pset_name, {})
            raw_val = pset_data.get(prop_name)
            if raw_val is None:
                continue
            literal = _xsd_literal(raw_val, rule["datatype"])
            triples.append(f"{rule['predicate']} {literal}")

        lines.append(f"<{bir_id}>")
        for i, triple in enumerate(triples):
            sep = " ;" if i < len(triples) - 1 else " ."
            lines.append(f"    {triple}{sep}")

        return "\n".join(lines) + "\n"
