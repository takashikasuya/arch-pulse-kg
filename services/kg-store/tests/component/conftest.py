"""Component test fixtures and auto-evidence generator for TC-COMP-KG-STORE-002."""
import json
import os
import time
import pytest
from fastapi.testclient import TestClient

from kg_store.main import create_app
from kg_store.adapters.pyoxigraph_mem import PyoxigraphMemRepository
from kg_store.adapters.null_publisher import NullPublisher


@pytest.fixture()
def mem_repo():
    return PyoxigraphMemRepository()


@pytest.fixture()
def null_pub():
    return NullPublisher()


@pytest.fixture()
def client(mem_repo, null_pub):
    app = create_app(repo=mem_repo, publisher=null_pub)
    with TestClient(app) as c:
        yield c


# ── Auto-evidence collection via pytest hook ─────────────────────────────────

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
        os.path.join(os.path.dirname(__file__), "../../evidence/TC-COMP-KG-STORE-002.json")
    )
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    overall = "PASS" if all(c["result"] == "PASS" for c in _TC_CASES) else "FAIL"
    with open(evidence_path, "w") as f:
        json.dump(
            {
                "id": "TC-COMP-KG-STORE-002",
                "verifies": [
                    "REQ-SOS-028",
                    "REQ-SOS-060",
                    "REQ-SOS-061",
                    "FUN-BIR-003",
                    "FUN-KG-001",
                    "FUN-KG-002",
                    "FUN-BIR-004",
                    "FUN-KG-003",
                    "IF-KG-TAGSEARCH",
                ],
                "type": "component",
                "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "overall_result": overall,
                "cases": _TC_CASES,
            },
            f,
            indent=2,
        )
