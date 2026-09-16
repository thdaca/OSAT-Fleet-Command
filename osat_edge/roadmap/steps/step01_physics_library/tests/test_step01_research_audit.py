"""Optional Pint, SymPy, and pydoe audit checks for Step01."""

from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from osat_edge.roadmap.steps.step01_physics_library import step01_physics_library as physics
from osat_edge.roadmap.steps.step01_physics_library.core.research_tools import (
    deterministic_factorial_design,
    spindle_residual_symbolic_identity_holds,
)
from osat_edge.roadmap.steps.step01_physics_library.core.units import (
    INTENTIONALLY_NONPHYSICAL_UNITS,
    assert_compatible_units,
    audit_declared_units,
    canonical_unit_expression,
    declared_unit_dimension,
)


@unittest.skipUnless(importlib.util.find_spec("pint"), "optional Pint audit dependency is not installed")
class Step01DimensionalAuditTests(unittest.TestCase):
    def test_all_declared_units_parse_or_are_documented_metadata(self) -> None:
        self.assertEqual(
            audit_declared_units(physics.PHYSICS_RELATIONS, physics.RESEARCH_CANDIDATES),
            (),
        )
        self.assertEqual(
            INTENTIONALLY_NONPHYSICAL_UNITS,
            {"state": "Categorical equipment or cycle state; not a physical quantity."},
        )

    def test_canonical_spellings_map_deterministically_without_mutation(self) -> None:
        self.assertEqual(canonical_unit_expression("RPM"), "revolution / minute")
        self.assertEqual(canonical_unit_expression("A/RPM"), "ampere * minute / revolution")
        self.assertEqual(canonical_unit_expression("mV"), "mV")
        self.assertEqual(physics.SPINDLE_RELATION.expected_units[0][1], "RPM")
        self.assertEqual(declared_unit_dimension("state"), "NONPHYSICAL_METADATA")

    def test_pint_rejects_incompatible_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "Incompatible dimensions"):
            assert_compatible_units("A", "RPM")


@unittest.skipUnless(importlib.util.find_spec("sympy"), "optional SymPy audit dependency is not installed")
class Step01SymbolicAuditTests(unittest.TestCase):
    def test_fixed_residual_identity_is_valid_without_equation_evaluation(self) -> None:
        self.assertTrue(spindle_residual_symbolic_identity_holds())


@unittest.skipUnless(importlib.util.find_spec("pydoe"), "optional pydoe research dependency is not installed")
class Step01ExperimentToolTests(unittest.TestCase):
    def test_explicit_factor_levels_create_a_deterministic_matrix(self) -> None:
        names, matrix = deterministic_factorial_design(
            {"speed_rpm": (20_000.0, 40_000.0), "feed_mm_s": (1.0, 2.0, 3.0)}
        )
        self.assertEqual(names, ("speed_rpm", "feed_mm_s"))
        np.testing.assert_array_equal(
            matrix,
            np.asarray(
                [
                    [20_000.0, 1.0],
                    [40_000.0, 1.0],
                    [20_000.0, 2.0],
                    [40_000.0, 2.0],
                    [20_000.0, 3.0],
                    [40_000.0, 3.0],
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()

