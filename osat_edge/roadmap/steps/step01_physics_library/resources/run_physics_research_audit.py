"""Run the optional Step01 physics-research audit profile."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys
import unittest
import warnings


EXPECTED_DEPENDENCIES = {
    "Pint": "0.25.3",
    "SymPy": "1.14.0",
    "pydoe": "1.5.0",
}
TEST_MODULE = (
    "osat_edge.roadmap.steps.step01_physics_library.tests."
    "test_step01_research_audit"
)


def main() -> int:
    warnings.simplefilter("error", ResourceWarning)
    mismatches: list[str] = []
    for distribution, expected in EXPECTED_DEPENDENCIES.items():
        try:
            installed = version(distribution)
        except PackageNotFoundError:
            mismatches.append(f"{distribution} is not installed")
            continue
        if installed != expected:
            mismatches.append(
                f"{distribution} must be {expected}, found {installed}"
            )
    if mismatches:
        for mismatch in mismatches:
            print(mismatch, file=sys.stderr)
        print(
            "Install resources/requirements-physics-research.txt first.",
            file=sys.stderr,
        )
        return 2

    project_root = Path(__file__).resolve().parents[5]
    sys.path.insert(0, str(project_root))
    suite = unittest.defaultTestLoader.loadTestsFromName(TEST_MODULE)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print("Research audit unexpectedly skipped optional checks.", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
