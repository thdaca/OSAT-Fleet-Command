"""Minimal command line for the student-facing current research build."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .common import RELEASE_CLASS, VERSION
from .demo import run_demo


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        prog="osat-edge",
        description=f"OSAT Fleet Command {VERSION} — {RELEASE_CLASS}",
    )
    value.add_argument("--version", action="version", version=VERSION)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run the deterministic nine-machine demo")
    replay = commands.add_parser(
        "reference-replay", help="Run the frozen synthetic reference replay"
    )
    replay.add_argument(
        "--dataset",
        default=None,
        help="Reference replay directory (defaults to the bundled frozen artifact)",
    )
    benchmark = commands.add_parser(
        "benchmark-nasa-milling",
        help="Analyze a local official NASA Milling artifact descriptively",
    )
    benchmark.add_argument("--dataset", required=True, help="Path to mill.mat, extracted directory, or official ZIP")
    benchmark.add_argument("--output", help="Optional path for the full JSON report")
    commands.add_parser("ui", help="Launch the PyQt6 research dashboard")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "demo":
        print(json.dumps(run_demo(), indent=2, sort_keys=True))
        return 0
    if args.command == "reference-replay":
        from .reference_replay import (
            DEFAULT_REFERENCE_DIRECTORY,
            ReferenceReplayError,
            run_reference_replay,
        )

        try:
            result = run_reference_replay(args.dataset or DEFAULT_REFERENCE_DIRECTORY)
        except ReferenceReplayError as exc:
            print(f"REFERENCE REPLAY ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "benchmark-nasa-milling":
        from .benchmark import (
            BenchmarkError,
            analyze_nasa_milling,
            benchmark_summary,
            write_benchmark_report,
        )

        try:
            result = analyze_nasa_milling(args.dataset)
            if args.output:
                write_benchmark_report(result, args.output)
        except BenchmarkError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(benchmark_summary(result), indent=2, sort_keys=True))
        return 0
    if args.command == "ui":
        from .ui import main as ui_main

        return ui_main()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
