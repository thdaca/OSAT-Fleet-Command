from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from osat_edge.common import EquipmentState, HealthState, RuntimeMode
from osat_edge.roadmap.step09_health_risk import HealthAssessment, SubsystemHealth
from osat_edge.roadmap.step10_fault_evidence import FaultEvidence, build_fault_evidence
from osat_edge.roadmap.step11a_maintenance_db import MaintenanceRepository
from osat_edge.roadmap.step11b_oem_manuals import load_oem_manuals
from osat_edge.roadmap.step12_rag import RetrievedPassage, retrieve_rag_context
from osat_edge.roadmap.step13_local_llm import generate_local_llm_json
from osat_edge.roadmap.step14_json_validation import deterministic_fallback, validate_llm_json
from osat_edge.roadmap.step15_maintenance_ticket import create_or_update_ticket, list_tickets
from support import NOW, identity, model_result


def critical_evidence(mode: RuntimeMode = RuntimeMode.SIMULATION) -> FaultEvidence:
    deviation = model_result(0.9).deviations[:1]
    assessment = HealthAssessment(
        identity(), NOW, mode, EquipmentState.PROCESSING, HealthState.CRITICAL,
        True, True,
        (SubsystemHealth("spindle", HealthState.CRITICAL, 0.9, deviation),),
        None, None, True,
    )
    result = build_fault_evidence(assessment)
    assert result is not None
    return result


class MaintenanceTests(unittest.TestCase):
    def test_normal_health_does_not_create_fault_evidence(self) -> None:
        assessment = HealthAssessment(
            identity(), NOW, RuntimeMode.SIMULATION, EquipmentState.PROCESSING,
            HealthState.NORMAL, True, True, (), None, None, False,
        )
        self.assertIsNone(build_fault_evidence(assessment))

    def test_fault_evidence_is_small_and_deterministic(self) -> None:
        evidence = critical_evidence()
        self.assertEqual(("spindle",), evidence.suspected_subsystems)
        self.assertIn("confirmed healthy", evidence.evidence_descriptions[0])

    def test_bundled_manuals_are_research_guidance(self) -> None:
        path = Path(__file__).resolve().parents[1] / "knowledge" / "maintenance_playbooks.json"
        chunks = load_oem_manuals(path)
        self.assertEqual(10, len(chunks))
        self.assertTrue(all("RESEARCH/DEMO" in chunk.text for chunk in chunks))

    def test_rag_keeps_same_family_and_fleet_guidance(self) -> None:
        path = Path(__file__).resolve().parents[1] / "knowledge" / "maintenance_playbooks.json"
        passages = retrieve_rag_context(critical_evidence(), (), load_oem_manuals(path), limit=10)
        ids = {passage.source_id for passage in passages}
        self.assertIn("wafer-saw-spindle", ids)
        self.assertIn("fleet-observe-only", ids)
        self.assertNotIn("wire-bond-head", ids)

    def test_absent_llm_uses_deterministic_fallback(self) -> None:
        evidence = critical_evidence()
        self.assertIsNone(generate_local_llm_json(evidence, (), model_path=None))
        result = validate_llm_json(None, evidence, ())
        self.assertEqual("deterministic-fallback", result.backend)

    def test_invalid_json_falls_back_and_valid_exact_schema_is_accepted(self) -> None:
        evidence = critical_evidence()
        bad = validate_llm_json('{"summary": "incomplete"}', evidence, ())
        raw = json.dumps({"summary": "Review", "likely_issue": "Not causal", "recommended_checks": ["Inspect approved path"]})
        good = validate_llm_json(raw, evidence, ())
        self.assertEqual("deterministic-fallback", bad.backend)
        self.assertEqual("local-llm", good.backend)

    def test_ticket_is_deduplicated_and_escalated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            degraded = replace(critical_evidence(), health_state=HealthState.DEGRADED)
            first = create_or_update_ticket(repository, degraded, deterministic_fallback(degraded, ()))
            critical = replace(critical_evidence(), timestamp=NOW.replace(second=10))
            second = create_or_update_ticket(repository, critical, deterministic_fallback(critical, ()))
            self.assertEqual(first.ticket_id, second.ticket_id)
            self.assertEqual("URGENT", second.priority)
            self.assertEqual(1, len(list_tickets(repository)))

    def test_live_or_replay_evidence_never_creates_actionable_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            for mode in (RuntimeMode.LIVE_EQUIPMENT, RuntimeMode.REAL_REPLAY):
                evidence = critical_evidence(mode)
                with self.subTest(mode=mode):
                    self.assertIsNone(create_or_update_ticket(repository, evidence, deterministic_fallback(evidence, ())))
            self.assertEqual([], repository.list_tickets())


if __name__ == "__main__":
    unittest.main()
