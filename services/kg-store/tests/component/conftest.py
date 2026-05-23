"""Component test fixtures and auto-evidence generator for TC-COMP-KG-STORE-002/003."""
import json
import os
import time
import pytest
from fastapi.testclient import TestClient

from kg_store.main import create_app
from kg_store.adapters.pyoxigraph_mem import PyoxigraphMemRepository
from kg_store.adapters.null_publisher import NullPublisher
import kg_store.config as _kg_config

_TEST_JWT_SECRET = "test-secret-replace-in-prod-min32b"


@pytest.fixture(autouse=True)
def _inject_tunnel_jwt_secret():
    original = _kg_config.settings.tunnel_jwt_secret
    _kg_config.settings.tunnel_jwt_secret = _TEST_JWT_SECRET
    yield
    _kg_config.settings.tunnel_jwt_secret = original


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


_EVIDENCE_IDS = [
    (
        "TC-COMP-KG-STORE-002",
        [
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
        None,  # None = include all tests
    ),
    (
        "TC-COMP-KG-STORE-003",
        ["REQ-SOS-056"],
        "test_dataspace_catalog",
    ),
]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _TC_CASES:
        return
    evidence_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../evidence")
    )
    os.makedirs(evidence_dir, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for tc_id, verifies, pattern in _EVIDENCE_IDS:
        cases = (
            _TC_CASES
            if pattern is None
            else [c for c in _TC_CASES if pattern in c["test_id"]]
        )
        if not cases:
            continue
        overall = "PASS" if all(c["result"] == "PASS" for c in cases) else "FAIL"
        with open(os.path.join(evidence_dir, f"{tc_id}.json"), "w") as f:
            json.dump(
                {
                    "id": tc_id,
                    "verifies": verifies,
                    "type": "component",
                    "run_timestamp": timestamp,
                    "overall_result": overall,
                    "cases": cases,
                },
                f,
                indent=2,
            )
