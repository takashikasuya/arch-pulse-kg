"""Port: IFC parser abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod
from ..domain.ifc_model import IfcEntity


class IfcParser(ABC):
    @abstractmethod
    def parse(self, data: bytes) -> list[IfcEntity]: ...
