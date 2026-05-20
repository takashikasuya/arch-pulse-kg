"""Test adapter: in-memory IFC parser backed by pre-built IfcEntity list."""
from __future__ import annotations
from ..domain.ifc_model import IfcEntity
from ..ports.ifc_parser import IfcParser


class MockIfcParser(IfcParser):
    def __init__(self, entities: list[IfcEntity]) -> None:
        self._entities = entities

    def parse(self, data: bytes) -> list[IfcEntity]:
        return list(self._entities)
