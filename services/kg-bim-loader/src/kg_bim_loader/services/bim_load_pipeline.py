"""BIM load pipeline — orchestrates parse → quality gate → BIR write → event publish."""
from __future__ import annotations
import time
from dataclasses import dataclass

from ..ports.ifc_parser import IfcParser
from ..ports.kg_store import KgStorePort
from ..ports.events import ChangeEventPublisher
from .quality_gate import QualityGateService
from .bir_mapper import BirMappingService


@dataclass
class LoadResult:
    total_entities: int
    quality_passed: bool


class BimLoadPipeline:
    def __init__(
        self,
        ifc_parser: IfcParser,
        kg_store: KgStorePort,
        publisher: ChangeEventPublisher,
    ) -> None:
        self._parser = ifc_parser
        self._kg_store = kg_store
        self._publisher = publisher
        self._gate = QualityGateService()
        self._mapper = BirMappingService()

    def run(self, data: bytes, tenant_id: str) -> LoadResult:
        entities = self._parser.parse(data)
        quality = self._gate.run(entities)
        if not quality.passed:
            return LoadResult(total_entities=len(entities), quality_passed=False)

        for entity in entities:
            turtle = self._mapper.to_turtle(entity, tenant_id)
            self._kg_store.write_turtle(turtle, tenant_id)

        tid_slug = tenant_id.replace(":", "-").replace("/", "-")
        subject = f"bldg.{tid_slug}.event.bim-load-completed"
        self._publisher.publish(
            subject,
            {
                "type": "bim-load-completed",
                "total_entities": len(entities),
                "tenant_id": tenant_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
        return LoadResult(total_entities=len(entities), quality_passed=True)
