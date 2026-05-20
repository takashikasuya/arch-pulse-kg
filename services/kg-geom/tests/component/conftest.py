"""Component test fixtures and auto-evidence generator for TC-COMP-KG-GEOM-001."""
import json
import os
import time
import pytest
from fastapi.testclient import TestClient

from kg_geom.main import create_app
from kg_geom.adapters.mem_geom import MemGeomRepository


@pytest.fixture()
def mem_repo():
    return MemGeomRepository()


@pytest.fixture()
def client(mem_repo):
    app = create_app(repo=mem_repo)
    with TestClient(app) as c:
        yield c


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


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _TC_CASES:
        return
    evidence_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../evidence/TC-COMP-KG-GEOM-001.json")
    )
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    overall = "PASS" if all(c["result"] == "PASS" for c in _TC_CASES) else "FAIL"
    with open(evidence_path, "w") as f:
        json.dump(
            {
                "id": "TC-COMP-KG-GEOM-001",
                "verifies": ["IF-KG-002", "REQ-SOS-005", "REQ-SOS-026"],
                "type": "component",
                "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "overall_result": overall,
                "cases": _TC_CASES,
            },
            f,
            indent=2,
        )
