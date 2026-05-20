"""Component test fixtures and auto-evidence generator for TC-COMP-KG-BIM-LOADER-001."""
import json
import os
import time
import pytest

from kg_bim_loader.services.quality_gate import QualityGateService
from kg_bim_loader.adapters.in_memory_kg_store import InMemoryKgStorePort
from kg_bim_loader.adapters.null_publisher import NullPublisher
from kg_bim_loader.services.bir_mapper import BirMappingService


@pytest.fixture()
def quality_gate():
    return QualityGateService()


@pytest.fixture()
def kg_store():
    return InMemoryKgStorePort()


@pytest.fixture()
def null_pub():
    return NullPublisher()


@pytest.fixture()
def bir_mapper():
    return BirMappingService()


# ── Auto-evidence collection ─────────────────────────────────────────────────

_TC_CASES: list[dict] = []


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call":
        return
    _TC_CASES.append(
        {
            "test_id": report.nodeid,
            "result": "PASS" if report.passed else "FAIL",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "detail": str(report.longrepr) if report.failed else "",
        }
    )


_EVIDENCE_IDS = [
    ("TC-COMP-KG-BIM-LOADER-001", ["REQ-SOS-026", "FUN-BIR-001", "FUN-BIR-002", "FUN-BIR-003", "FUN-BIR-004"]),
    ("TC-COMP-KG-BIM-LOADER-002", ["REQ-SOS-028", "FUN-BIR-001", "FUN-BIR-002", "FUN-BIR-003", "FUN-BIR-004"]),
    ("TC-COMP-KG-BIM-LOADER-003", ["REQ-SOS-032", "FUN-BIR-001", "FUN-BIR-002", "FUN-BIR-003", "FUN-BIR-004"]),
]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _TC_CASES:
        return
    evidence_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../evidence")
    )
    os.makedirs(evidence_dir, exist_ok=True)
    overall = "PASS" if all(c["result"] == "PASS" for c in _TC_CASES) else "FAIL"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for tc_id, verifies in _EVIDENCE_IDS:
        with open(os.path.join(evidence_dir, f"{tc_id}.json"), "w") as f:
            json.dump(
                {
                    "id": tc_id,
                    "verifies": verifies,
                    "type": "component",
                    "run_timestamp": timestamp,
                    "overall_result": overall,
                    "cases": _TC_CASES,
                },
                f,
                indent=2,
            )
