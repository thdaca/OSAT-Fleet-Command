"""Core structural and compatibility checks for the Step01 foundation."""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

from osat_edge.roadmap.steps.step01_physics_library import step01_physics_library as physics

EXPECTED_PUBLIC_API = (
    "ALL_MACHINE_FAMILIES",
    "AlignedSignals",
    "ApplicabilityEnvelope",
    "CalibrationReport",
    "EvidenceClaim",
    "EvidenceMaturity",
    "ExperimentPlan",
    "FaultSensitivity",
    "INTERCEPT",
    "MeasurementRequirement",
    "MeasurementStatus",
    "PHYSICS_RELATIONS",
    "ParameterSource",
    "ParameterSpec",
    "ParameterStabilityDiagnostics",
    "PhysicsReadinessEntry",
    "PhysicsRelation",
    "RESEARCH_CANDIDATES",
    "RESEARCH_REFERENCES",
    "RESIDUAL_SCALE",
    "ReferenceType",
    "RelationCompute",
    "RelationFit",
    "RelationKind",
    "RelationStatus",
    "ResearchCandidate",
    "ResearchReference",
    "ResidualDiagnostics",
    "ResidualDirection",
    "ResidualFmeaEntry",
    "SLOPE",
    "SPEED_HIGH",
    "SPEED_LOW",
    "SPEED_SPAN",
    "SPINDLE_EXPERIMENT",
    "SPINDLE_MEASUREMENTS",
    "SPINDLE_PARAMETERS",
    "SPINDLE_RELATION",
    "SensorFailureMode",
    "UncertaintyCategory",
    "UncertaintySource",
    "ValidationDiagnostics",
    "ValidationEvidence",
    "audit_physics_library",
    "calibrate_relation",
    "contact_resistance_mohm_for_research",
    "physics_readiness_report",
    "propagate_linearized_uncertainty",
    "relations_for_family",
    "research_catalog_for_family",
    "residual_diagnostics",
    "validate_relation_calibration",
)

EXPECTED_FAMILIES = (
    "wafer_mount",
    "wafer_saw",
    "die_attach",
    "wire_bond",
    "molding",
    "marking",
    "trim_form",
    "singulation",
    "final_test",
)

EXPECTED_CANDIDATE_IDS = (
    "wafer_mount.roller_current_web_tension",
    "wafer_saw.coolant_hydraulic_resistance",
    "die_attach.nozzle_vacuum_leak_rate",
    "wire_bond.ultrasonic_input_impedance",
    "molding.clamp_cavity_force_balance",
    "marking.laser_output_drive_temperature",
    "trim_form.motor_current_punch_force",
    "singulation.spindle_current_speed_residual",
    "final_test.contact_resistance",
)

EXPECTED_RECORD_HASHES = {
    "relations": "0b54bd0714688764c71f524ddd9e0ccecac6449771ad9894c44f8844dec98fda",
    "candidates": "710e08aabacec1f5ae727481d5a75dce8ad93a99deeefeac3d3995fba65e5ab7",
    "references": "02adbf8cc380b24bde3aa23945b19465bd0b88179d8038d362743ed8e163f809",
    "readiness": "48ecf564e801cf3e8b0b5e54f5aa4783ccb5e68b0c1ef81985aed317b6850ebd",
}


def _semantic_value(value: object) -> object:
    if dataclasses.is_dataclass(value):
        return {
            field.name: _semantic_value(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if field.name not in {"compute", "fit"}
        }
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_semantic_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_semantic_value(item) for item in value)
    if isinstance(value, dict):
        return {str(key): _semantic_value(item) for key, item in value.items()}
    return value


def _semantic_hash(value: object) -> str:
    payload = json.dumps(
        _semantic_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Step01FoundationCompatibilityTests(unittest.TestCase):
    def test_public_step01_api_is_explicit_and_frozen(self) -> None:
        self.assertEqual(physics.__all__, EXPECTED_PUBLIC_API)
        self.assertTrue(all(hasattr(physics, name) for name in physics.__all__))
        self.assertTrue(
            {"np", "HuberRegressor", "dataclass", "Callable", "Mapping", "Sequence"}.isdisjoint(
                physics.__all__
            )
        )

    def test_optional_research_profile_is_isolated_and_pinned(self) -> None:
        project_root = Path(__file__).resolve().parents[5]
        step_root = Path(__file__).resolve().parents[1]
        root_requirements = (project_root / "requirements.txt").read_text(
            encoding="utf-8"
        ).lower()
        self.assertNotIn("pint", root_requirements)
        self.assertNotIn("sympy", root_requirements)
        self.assertNotIn("pydoe", root_requirements)
        self.assertEqual(
            (
                step_root / "resources" / "requirements-physics-research.txt"
            ).read_text(encoding="utf-8").strip().splitlines(),
            ["Pint==0.25.3", "SymPy==1.14.0", "pydoe==1.5.0"],
        )
        self.assertTrue(
            (step_root / "resources" / "run_physics_research_audit.py").is_file()
        )
        inventory = (
            step_root / "resources" / "DEPENDENCY_IP_INVENTORY.md"
        ).read_text(encoding="utf-8")
        for package in ("Pint", "SymPy", "pydoe", "BSD"):
            self.assertIn(package, inventory)

    def test_references_tools_and_experiments_have_narrow_owners(self) -> None:
        evidence = importlib.import_module(
            "osat_edge.roadmap.steps.step01_physics_library.core.evidence"
        )
        references = importlib.import_module(
            "osat_edge.roadmap.steps.step01_physics_library.core.references"
        )
        research_tools = importlib.import_module(
            "osat_edge.roadmap.steps.step01_physics_library.core.research_tools"
        )
        self.assertIs(references.RESEARCH_REFERENCES, physics.RESEARCH_REFERENCES)
        self.assertFalse(hasattr(evidence, "ISO_DIAGNOSTICS"))
        self.assertFalse(hasattr(evidence, "deterministic_factorial_design"))
        self.assertTrue(hasattr(research_tools, "deterministic_factorial_design"))

        experiment_names = {
            "wafer_mount": "WEB_EXPERIMENT",
            "wafer_saw": "COOLANT_EXPERIMENT",
            "die_attach": "VACUUM_EXPERIMENT",
            "wire_bond": "WIRE_EXPERIMENT",
            "molding": "MOLD_EXPERIMENT",
            "marking": "LASER_EXPERIMENT",
            "trim_form": "PRESS_EXPERIMENT",
            "singulation": "SINGULATION_EXPERIMENT",
            "final_test": "CONTACT_EXPERIMENT",
        }
        candidates = {candidate.family: candidate for candidate in physics.RESEARCH_CANDIDATES}
        for family, experiment_name in experiment_names.items():
            module = importlib.import_module(
                f"osat_edge.roadmap.steps.step01_physics_library.families.{family}"
            )
            self.assertIs(candidates[family].experiment_plan, getattr(module, experiment_name))

    def test_family_and_record_ids_are_frozen(self) -> None:
        self.assertEqual(physics.ALL_MACHINE_FAMILIES, EXPECTED_FAMILIES)
        self.assertEqual(
            tuple(relation.relation_id for relation in physics.PHYSICS_RELATIONS),
            ("spindle.current_speed_residual",),
        )
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in physics.RESEARCH_CANDIDATES),
            EXPECTED_CANDIDATE_IDS,
        )

    def test_status_maturity_references_and_claims_are_frozen(self) -> None:
        records = {
            "relations": physics.PHYSICS_RELATIONS,
            "candidates": physics.RESEARCH_CANDIDATES,
            "references": physics.RESEARCH_REFERENCES,
            "readiness": physics.physics_readiness_report(),
        }
        self.assertEqual(
            {name: _semantic_hash(value) for name, value in records.items()},
            EXPECTED_RECORD_HASHES,
        )
        self.assertEqual(physics.audit_physics_library(), ())

    def test_all_nine_families_have_one_obvious_owner_module(self) -> None:
        step_root = Path(physics.__file__).resolve().parent
        for family in EXPECTED_FAMILIES:
            self.assertTrue((step_root / "families" / f"{family}.py").is_file())
            self.assertTrue(physics.research_catalog_for_family(family))

    def test_normal_edge_import_does_not_need_research_packages(self) -> None:
        code = """
import builtins
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split('.', 1)[0].lower() in {'pint', 'sympy', 'pydoe'}:
        raise AssertionError(f'optional research dependency imported: {name}')
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
import osat_edge.pipeline
import osat_edge.roadmap.steps.step01_physics_library.step01_physics_library
"""
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[5],
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_ws01_fitting_and_residual_are_exactly_frozen(self) -> None:
        speed = np.linspace(20_000.0, 40_000.0, 60)
        current = 1.4 + 3.1e-5 * speed + 0.002 * np.sin(np.arange(60, dtype=float))
        parameters = dict(
            physics.SPINDLE_RELATION.fit(
                {"spindle_speed": speed, "spindle_current": current}
            )
        )
        self.assertEqual(
            {name: value.hex() for name, value in parameters.items()},
            {
                physics.SLOPE: "0x1.040f98d10da1ep-15",
                physics.INTERCEPT: "0x1.6668b1df93fa5p+0",
                physics.RESIDUAL_SCALE: "0x1.0ae8f9e795a92p-9",
                physics.SPEED_SPAN: "0x1.28e0000000000p+14",
                physics.SPEED_LOW: "0x1.4050000000000p+14",
                physics.SPEED_HIGH: "0x1.3498000000000p+15",
            },
        )
        evaluation_speed = np.asarray([25_000.0, 30_000.0, 35_000.0])
        evaluation_current = 1.4 + 3.1e-5 * evaluation_speed + np.asarray([0.01, 0.02, 0.03])
        result = physics.SPINDLE_RELATION.compute(
            {
                "spindle_speed": evaluation_speed,
                "spindle_current": evaluation_current,
            },
            parameters,
        )
        self.assertEqual(
            result["spindle.electromechanical_load_residual_a.median"].hex(),
            "0x1.46480c6831100p-6",
        )

    def test_calibration_diagnostics_uncertainty_and_catalog_are_exactly_frozen(self) -> None:
        speed = np.linspace(20_000.0, 40_000.0, 60)
        current = 1.4 + 3.1e-5 * speed + 0.002 * np.sin(np.arange(60, dtype=float))
        calibration = physics.calibrate_relation(
            "spindle.current_speed_residual",
            {"spindle_speed": speed, "spindle_current": current},
            blocks=3,
        )
        self.assertEqual(
            _semantic_hash(calibration),
            "a2b467f5fa33688826907b39a8a78125593c1815d09b65f07fe9e42e12812c7b",
        )

        diagnostics = physics.residual_diagnostics(
            np.asarray([0.1, -0.2, 0.3, 0.4, -0.5]),
            np.asarray([1.0, 2.0, 3.0, 4.0, 5.0]),
            np.asarray([False, True, False, False, True]),
        )
        self.assertEqual(
            tuple(
                value.hex() if isinstance(value, float) else value
                for value in dataclasses.astuple(diagnostics)
            ),
            (
                5,
                "0x1.0000000000000p+0",
                "0x1.999999999999ap-4",
                "0x1.3333333333334p-2",
                "0x1.6666666666666p-2",
                "-0x1.eb851eb851eb9p-5",
                "-0x1.e688c42720766p-2",
                "0x1.e688c42720766p-2",
                "0x1.999999999999ap-2",
            ),
        )
        uncertainty = physics.propagate_linearized_uncertainty(
            np.asarray([2.0, -1.0]),
            np.asarray([[0.04, 0.01], [0.01, 0.09]]),
        )
        self.assertEqual(uncertainty.hex(), "0x1.d54178e8830d6p-2")

        catalogs = tuple(
            (
                family,
                tuple(
                    getattr(record, "relation_id", getattr(record, "candidate_id", ""))
                    for record in physics.research_catalog_for_family(family)
                ),
            )
            for family in EXPECTED_FAMILIES
        )
        self.assertEqual(
            catalogs,
            (
                ("wafer_mount", ("wafer_mount.roller_current_web_tension",)),
                (
                    "wafer_saw",
                    (
                        "spindle.current_speed_residual",
                        "wafer_saw.coolant_hydraulic_resistance",
                    ),
                ),
                ("die_attach", ("die_attach.nozzle_vacuum_leak_rate",)),
                ("wire_bond", ("wire_bond.ultrasonic_input_impedance",)),
                ("molding", ("molding.clamp_cavity_force_balance",)),
                ("marking", ("marking.laser_output_drive_temperature",)),
                ("trim_form", ("trim_form.motor_current_punch_force",)),
                ("singulation", ("singulation.spindle_current_speed_residual",)),
                ("final_test", ("final_test.contact_resistance",)),
            ),
        )



if __name__ == "__main__":
    unittest.main()
