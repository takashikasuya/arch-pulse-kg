"""Component test fixtures for CS-AI-GRAPHRAG."""
import json
import os
import pytest
from fastapi.testclient import TestClient

from graphrag.main import create_app
from graphrag.adapters.stub_kg_reader import StubKgReader
from graphrag.adapters.null_ts_reader import NullTsReader
from graphrag.adapters.null_llm_gateway import NullLlmGateway


SPACE_BIR_ID = "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"
DEVICE_BIR_ID = "urn:bir:device:6ba7b810-9dad-11d1-80b4-00c04fd430c8"
POINT_BIR_ID = "urn:bir:point:aaaabbbb-cccc-dddd-eeee-ffffffffffff"
BIR_NS = "https://arch-pulse.example/ns/bir#"

SAMPLE_BINDINGS = [
    {
        "s": {"type": "uri", "value": SPACE_BIR_ID},
        "p": {"type": "uri", "value": f"{BIR_NS}contains"},
        "o": {"type": "uri", "value": DEVICE_BIR_ID},
    },
    {
        "s": {"type": "uri", "value": DEVICE_BIR_ID},
        "p": {"type": "uri", "value": f"{BIR_NS}hasPoint"},
        "o": {"type": "uri", "value": POINT_BIR_ID},
    },
]


@pytest.fixture()
def stub_kg():
    return StubKgReader(bindings=SAMPLE_BINDINGS)


@pytest.fixture()
def empty_kg():
    return StubKgReader(bindings=[])


@pytest.fixture()
def null_ts():
    return NullTsReader()


@pytest.fixture()
def null_llm():
    return NullLlmGateway()


@pytest.fixture()
def client(stub_kg, null_ts, null_llm):
    app = create_app(kg=stub_kg, ts=null_ts, llm=null_llm)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def empty_client(empty_kg, null_ts, null_llm):
    app = create_app(kg=empty_kg, ts=null_ts, llm=null_llm)
    with TestClient(app) as c:
        yield c


# ── Evidence collection ──────────────────────────────────────────────────────

_results: list[dict] = []


def pytest_runtest_logreport(report):
    if report.when == "call":
        _results.append({
            "test": report.nodeid,
            "outcome": report.outcome,
            "duration": round(report.duration, 3),
        })


def pytest_sessionfinish(session, exitstatus):
    os.makedirs("evidence", exist_ok=True)
    evidence = {
        "tc_id": "TC-COMP-AI-GRAPHRAG-001",
        "verifies": ["REQ-SOS-022", "FUN-ENERGY-002", "FUN-ENERGY-003"],
        "results": _results,
        "summary": {
            "total": len(_results),
            "passed": sum(1 for r in _results if r["outcome"] == "passed"),
            "failed": sum(1 for r in _results if r["outcome"] == "failed"),
        },
    }
    with open("evidence/TC-COMP-AI-GRAPHRAG-001.json", "w") as f:
        json.dump(evidence, f, indent=2)
