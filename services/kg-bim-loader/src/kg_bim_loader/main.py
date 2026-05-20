"""CLI entry point for bim-loader.

Exit codes:
  0 — success
  1 — quality gate failure
  2 — other error (I/O, network, etc.)

NOTE: Production use requires replacing MockIfcParser with an IfcOpenShellParser adapter.
This stub intentionally refuses to load when no real parser is wired (see --dry-run below).
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
    parser.add_argument("--report", type=Path, default=None, help="Quality report output path (written on failure)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and quality-check only; do not write to KG-STORE",
    )
    args = parser.parse_args(argv)

    try:
        data = args.ifc.read_bytes()
    except OSError as e:
        print(f"Error reading IFC file: {e}", file=sys.stderr)
        sys.exit(2)

    # TODO: replace MockIfcParser with IfcOpenShellParser when ifcopenshell is available.
    # Until then, bim-loader operates in quality-check-only mode (0 entities parsed).
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
        if args.report and result.quality_result is not None:
            result.quality_result.write_report(args.report)
            print(f"Report written to: {args.report}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {result.total_entities} entities.")
