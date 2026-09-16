"""Minimal command line for the student-facing 0.2.0 build."""

from __future__ import annotations

import argparse
import json
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
    commands.add_parser("ui", help="Launch the PyQt6 research dashboard")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "demo":
        print(json.dumps(run_demo(), indent=2, sort_keys=True))
        return 0
    if args.command == "ui":
        from .ui import main as ui_main

        return ui_main()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
