"""Quality gate result domain types."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Violation:
    ifc_guid: str
    violation_type: str  # sliver | gap | reversed_normals | missing_required_attr
    detail: str


@dataclass
class QualityResult:
    passed: bool
    violations: list[Violation] = field(default_factory=list)

    def write_report(self, path: Path) -> None:
        report = {
            "passed": self.passed,
            "violations": [
                {
                    "ifc_guid": v.ifc_guid,
                    "violation_type": v.violation_type,
                    "detail": v.detail,
                }
                for v in self.violations
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
