"""CLI entry point for bim-loader.

Exit codes:
  0 — success
  1 — quality gate failure
  2 — other error (I/O, network, etc.)
"""
from __future__ import annotations
import sys
import argparse
from pathlib import Path

from .adapters.http_kg_store import HttpKgStorePort
from .adapters.null_publisher import NullPublisher
from .adapters.mock_ifc_parser import MockIfcParser
from .services.bim_load_pipeline import BimLoadPipeline


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bim-loader")
    parser.add_argument("--ifc", type=Path, required=True, help="Path to IFC file")
    parser.add_argument("--tenant", required=True, help="Tenant URN")
    parser.add_argument("--kg-store-url", default="http://localhost:8000", help="CS-KG-STORE base URL")
    parser.add_argument("--report", type=Path, default=None, help="Quality report output path")
    args = parser.parse_args(argv)

    try:
        data = args.ifc.read_bytes()
    except OSError as e:
        print(f"Error reading IFC file: {e}", file=sys.stderr)
        sys.exit(2)

    # In production, replace MockIfcParser with IfcOpenShellParser adapter
    ifc_parser = MockIfcParser([])
    kg_store = HttpKgStorePort(args.kg_store_url)
    publisher = NullPublisher()

    pipeline = BimLoadPipeline(ifc_parser=ifc_parser, kg_store=kg_store, publisher=publisher)
    try:
        result = pipeline.run(data, args.tenant)
    except Exception as e:
        print(f"Error during BIM load: {e}", file=sys.stderr)
        sys.exit(2)

    if not result.quality_passed:
        print("Quality gate FAILED", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {result.total_entities} entities.")
