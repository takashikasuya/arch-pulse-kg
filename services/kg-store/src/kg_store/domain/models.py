from __future__ import annotations
from pydantic import BaseModel, Field


class ExternalRefs(BaseModel):
    ifc_guid: str | None = None
    revit_element_id: str | None = None
    gbxml_space_id: str | None = None
    energyplus_zone: str | None = None
    p223_space_uri: str | None = None
    bas_point_prefix: str | None = None
    brick_uri: str | None = None


class BirLookupResult(BaseModel):
    bir_id: str
    kind: str
    status: str
    external_refs: ExternalRefs


class DcatPeriod(BaseModel):
    start: str
    end: str


class DcatChecksum(BaseModel):
    algorithm: str
    value: str


class DcatDataset(BaseModel):
    dataset_uri: str
    tenant_scope: str
    data_class: str
    opt_in_job_id: str
    period: DcatPeriod
    byte_size: int
    checksum: DcatChecksum
    was_derived_from: str
    bucket: str | None = None
    aggregation_functions: list[str] | None = None
    backend_hint: str | None = None


class ShaclValidationResult(BaseModel):
    conforms: bool
    report_turtle: str
    violations: list[dict] = Field(default_factory=list)
