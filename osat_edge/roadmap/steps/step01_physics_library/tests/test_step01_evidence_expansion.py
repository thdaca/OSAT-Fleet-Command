"""Regression checks for the 0.2.5 Step01 evidence expansion."""

from __future__ import annotations

from pathlib import Path
import unittest

from osat_edge.roadmap.pre_steps.pre01_common.contracts import DataOrigin
from osat_edge.roadmap.steps.step01_physics_library import library as physics


FAMILIES = (
    "wafer_mount", "wafer_saw", "die_attach", "wire_bond", "molding",
    "marking", "trim_form", "singulation", "final_test",
)
DOSSIER_SECTIONS = (
    "## Mechanism",
    "## Candidate measurable relation",
    "## Exact variables and units",
    "## Available OEM/process signals",
    "## Confounders",
    "## Parameter identifiability",
    "## Calibration domain",
    "## Uncertainty sources",
    "## Falsification criteria",
    "## Minimum machine experiment",
    "## Source quality",
    "## Measurement-semantics maturity",
    "## Status",
)


class Step01EvidenceExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.step_root = Path(physics.__file__).resolve().parent
        cls.research_root = cls.step_root / "research"

    def test_each_family_has_one_complete_owned_dossier(self) -> None:
        actual = tuple(sorted(path.name for path in self.research_root.iterdir() if path.is_dir()))
        self.assertEqual(tuple(sorted(FAMILIES)), actual)
        for family in FAMILIES:
            with self.subTest(family=family):
                dossier = (self.research_root / family / "DOSSIER.md").read_text(encoding="utf-8")
                for section in DOSSIER_SECTIONS:
                    self.assertIn(section, dossier)

    def test_research_evidence_tiers_are_explicit_and_nonoperational(self) -> None:
        self.assertEqual(
            tuple(item.value for item in physics.ResearchEvidenceTier),
            (
                "PUBLISHED_REAL_OSAT_STUDY",
                "REQUESTABLE_REAL_OSAT_DATA",
                "EXECUTED_REAL_OSAT_DATA",
            ),
        )
        self.assertTrue(
            set(item.value for item in physics.ResearchEvidenceTier).isdisjoint(
                item.value for item in DataOrigin
            )
        )

    def test_only_the_frozen_wafer_saw_equation_is_executable(self) -> None:
        self.assertEqual(1, len(physics.PHYSICS_RELATIONS))
        relation = physics.PHYSICS_RELATIONS[0]
        self.assertEqual("spindle.current_speed_residual", relation.relation_id)
        self.assertEqual(frozenset({"wafer_saw"}), relation.machine_families)
        self.assertEqual(
            "r_I = I_reported - (a_machine n_actual + b_machine), evaluated only inside the calibrated speed envelope",
            relation.equation,
        )
        self.assertEqual(physics.RelationStatus.RUNTIME_RESEARCH, relation.status)
        self.assertEqual(physics.EvidenceMaturity.LITERATURE_SUPPORTED, relation.evidence_maturity)
        wording = f"{relation.description} {relation.mechanism}".lower()
        self.assertIn("electromechanical spindle-load consistency residual", wording)
        self.assertNotIn("cutting force", wording)

    def test_new_literature_candidates_never_become_runtime(self) -> None:
        statuses = {item.candidate_id: item.status for item in physics.RESEARCH_CANDIDATES}
        self.assertEqual(physics.RelationStatus.REJECTED, statuses["die_attach.nozzle_vacuum_leak_rate"])
        self.assertEqual(physics.RelationStatus.REJECTED, statuses["wire_bond.ultrasonic_input_impedance"])
        for candidate_id in (
            "die_attach.closed_loop_force_z_temperature_consistency",
            "wire_bond.ultrasonic_generator_electrical_load_consistency",
            "molding.clamp_transfer_temperature_consistency",
            "marking.commanded_measured_laser_output_stability",
            "trim_form.stroke_aligned_servo_load_profile_consistency",
            "singulation.spindle_current_speed_residual",
            "final_test.handler_motor_signature_consistency",
        ):
            self.assertEqual(physics.RelationStatus.RESEARCH_ONLY, statuses[candidate_id])

    def test_ws_and_sg_identity_and_calibration_remain_separate(self) -> None:
        self.assertEqual((physics.SPINDLE_RELATION,), physics.relations_for_family("wafer_saw"))
        self.assertEqual((), physics.relations_for_family("singulation"))
        singulation = next(
            item for item in physics.RESEARCH_CANDIDATES
            if item.candidate_id == "singulation.spindle_current_speed_residual"
        )
        joined = " ".join((singulation.description, singulation.decision_reason, singulation.major_blocker)).lower()
        self.assertIn("sg", joined)
        self.assertIn("ws-01", joined)
        self.assertIn("separate", joined)

    def test_named_sources_are_present_with_resolved_identifiers(self) -> None:
        identifiers = {item.key: item.identifier for item in physics.RESEARCH_REFERENCES}
        expected = {
            "infineon_dicing_tape_tension": "EP3705862B1 / US20200286795A1",
            "disco_dad3660": "https://www.disco.co.jp/jp/products/dicer/dad3660.html",
            "pti_wire_bond_2026": "10.32604/cmc.2026.078762",
            "roy_2026_final_test_handler": "10.1016/j.cie.2026.111872",
            "st_awfd": "https://github.com/STMicroelectronics/ST-AWFD",
            "tuhh_dad3350_2026": "10.15480/882.15763",
            "chdl_2025": "arXiv:2507.06738",
            "amkor_atep_2022": "hdl:10400.22/20698",
            "ase_wire_bond_aoi_2025": "etd-0609125-111038",
            "ase_drilling_aoi_2024": "arXiv:2404.05183 / 10.1109/ICCE63647.2025.10930135",
        }
        for key, identifier in expected.items():
            self.assertEqual(identifier, identifiers[key])

    def test_pti_fields_and_request_boundary_are_exact(self) -> None:
        dossier = (self.research_root / "wire_bond" / "DOSSIER.md").read_text(encoding="utf-8")
        request = (self.research_root / "wire_bond" / "WB04_DATA_REQUEST.md").read_text(encoding="utf-8")
        for field in (
            "Capillary Count", "Bond Height Delta", "Deformation", "Die Height",
            "Die Tilt", "Bond Force", "USG Impedance", "USG Current",
            "Z at Contact", "Z at End of Bonding",
        ):
            self.assertIn(field, dossier)
        self.assertIn("Do not request or accept customer or product identity", request)
        self.assertIn("independently adjudicated healthy/fault intervals", request)
        self.assertIn("machine/OEM definition", request)

    def test_catalog_never_represents_paper_only_material_as_executed(self) -> None:
        catalog = (self.research_root / "EVIDENCE_CATALOG.md").read_text(encoding="utf-8")
        self.assertIn("`EXECUTED_REAL_OSAT_DATA`: **none**", catalog)
        self.assertIn("A paper is never treated as raw telemetry", catalog)
        self.assertIn("no public raw records", catalog)
        self.assertIn("not machine-health validation", catalog)

    def test_ase_wire_bond_and_drilling_evidence_are_not_conflated(self) -> None:
        catalog = (self.research_root / "EVIDENCE_CATALOG.md").read_text(encoding="utf-8")
        wire_bond = next(
            item for item in physics.RESEARCH_REFERENCES
            if item.key == "ase_wire_bond_aoi_2025"
        )
        drilling = next(
            item for item in physics.RESEARCH_REFERENCES
            if item.key == "ase_drilling_aoi_2024"
        )
        self.assertIn("embargoed until 2035", wire_bond.scope_limitations)
        self.assertIn("no public sample count", wire_bond.scope_limitations)
        self.assertNotIn("455", wire_bond.supports)
        self.assertIn("455 samples", drilling.supports)
        self.assertIn("drilling-process", drilling.supports)
        self.assertIn(
            "these counts belong only to the drilling dataset",
            " ".join(catalog.lower().split()),
        )


if __name__ == "__main__":
    unittest.main()
