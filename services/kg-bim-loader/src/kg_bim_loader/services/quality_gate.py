"""Quality gate service — validates IFC entities before BIR conversion."""
from __future__ import annotations
from ..domain.ifc_model import IfcEntity
from ..domain.quality_result import QualityResult, Violation

_SLIVER_THRESHOLD_M2 = 0.001  # faces smaller than 1 cm² are slivers
_GAP_THRESHOLD_MM = 5.0       # boundary gaps larger than 5 mm are rejected

# Dot product threshold: normal · (0,0,-1) > 0.99 means nearly straight-down,
# which is invalid for floor-plane faces expected to face upward.
_REVERSED_NORMAL_THRESHOLD = 0.99


class QualityGateService:
    def run(self, entities: list[IfcEntity]) -> QualityResult:
        violations: list[Violation] = []
        for entity in entities:
            violations.extend(self._check(entity))
        return QualityResult(passed=len(violations) == 0, violations=violations)

    def _check(self, entity: IfcEntity) -> list[Violation]:
        violations: list[Violation] = []

        if not entity.ifc_guid:
            violations.append(
                Violation(
                    ifc_guid=entity.ifc_guid,
                    violation_type="missing_required_attr",
                    detail="IfcGloballyUniqueId is empty",
                )
            )

        for face in entity.faces:
            if face.area < _SLIVER_THRESHOLD_M2:
                violations.append(
                    Violation(
                        ifc_guid=entity.ifc_guid,
                        violation_type="sliver",
                        detail=f"face area {face.area:.6f} m² < threshold {_SLIVER_THRESHOLD_M2} m²",
                    )
                )
            nx, ny, nz = face.normal
            if nz < -_REVERSED_NORMAL_THRESHOLD:
                violations.append(
                    Violation(
                        ifc_guid=entity.ifc_guid,
                        violation_type="reversed_normals",
                        detail=f"face normal {face.normal} points downward (nz={nz:.3f})",
                    )
                )

        if entity.boundary_gaps > _GAP_THRESHOLD_MM:
            violations.append(
                Violation(
                    ifc_guid=entity.ifc_guid,
                    violation_type="gap",
                    detail=f"boundary gap {entity.boundary_gaps:.1f} mm > threshold {_GAP_THRESHOLD_MM} mm",
                )
            )

        return violations
