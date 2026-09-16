from __future__ import annotations

import json
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from osat_edge.common import EquipmentState, HealthState, RuntimeMode
from osat_edge.roadmap.step07_machine_model import FeatureDeviation
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

    def test_fault_evidence_is_localized_bounded_and_signed(self) -> None:
        deviations = (
            FeatureDeviation("spindle_current.median", "spindle", "location", 9.0, 5.0, 4.0, 0.9),
            FeatureDeviation("spindle.residual", "spindle", "physics", -0.2, 0.0, -3.0, 0.8),
            FeatureDeviation("coolant_pressure.median", "cooling", "location", 99.0, 1.0, 20.0, 0.99),
        )
        assessment = HealthAssessment(
            identity(), NOW, RuntimeMode.SIMULATION, EquipmentState.PROCESSING,
            HealthState.CRITICAL, True, True,
            (
                SubsystemHealth("spindle", HealthState.CRITICAL, 0.9, deviations[:2]),
                SubsystemHealth("cooling", HealthState.NORMAL, 0.1, deviations[2:]),
            ),
            None, None, True,
        )
        evidence = build_fault_evidence(assessment)
        self.assertIsNotNone(evidence)
        descriptions = evidence.evidence_descriptions
        self.assertLessEqual(len(descriptions), 6)
        self.assertTrue(all("spindle" in item for item in descriptions))
        self.assertTrue(any("+" in item and "above" in item for item in descriptions))
        self.assertTrue(any("-" in item and "below" in item for item in descriptions))

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

    def test_rag_zero_limit_and_empty_vocabulary_are_boring(self) -> None:
        evidence = critical_evidence()
        self.assertEqual((), retrieve_rag_context(evidence, ("prior" ,), (), limit=0))
        result = retrieve_rag_context(evidence, ("!!!", "..."), (), limit=1)
        self.assertEqual((RetrievedPassage("maintenance:0", "!!!"),), result)

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

    def test_control_only_and_bidi_control_prose_fall_back(self) -> None:
        evidence = critical_evidence()
        for attack in ("\u0001\u0002", "\u202e\u2066\u2069"):
            raw = json.dumps(
                {
                    "summary": attack,
                    "likely_issue": "Issue",
                    "recommended_checks": ["Check"],
                }
            )
            with self.subTest(attack=repr(attack)):
                self.assertEqual(
                    "deterministic-fallback",
                    validate_llm_json(raw, evidence, ()).backend,
                )

    def test_international_unicode_and_joiners_survive_sanitization(self) -> None:
        evidence = critical_evidence()
        summary = "ملخص فحص المحور"
        issue = "می‌پیوندد"  # Contains U+200C ZERO WIDTH NON-JOINER.
        check = "Inspect family 👩‍🔧 assembly"  # Emoji sequence contains U+200D.
        raw = json.dumps(
            {
                "summary": summary,
                "likely_issue": issue,
                "recommended_checks": [check],
            },
            ensure_ascii=False,
        )
        result = validate_llm_json(raw, evidence, ())
        self.assertEqual("local-llm", result.backend)
        self.assertEqual(summary, result.summary)
        self.assertIn("\u200c", result.likely_issue)
        self.assertIn("\u200d", result.recommended_checks[0])

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

    def test_unresolved_ticket_never_automatically_downgrades(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            critical = critical_evidence()
            first = create_or_update_ticket(
                repository, critical, deterministic_fallback(critical, ())
            )
            degraded = replace(
                critical,
                timestamp=NOW.replace(second=10),
                health_state=HealthState.DEGRADED,
            )
            second = create_or_update_ticket(
                repository, degraded, deterministic_fallback(degraded, ())
            )
            self.assertEqual(first.ticket_id, second.ticket_id)
            self.assertEqual("CRITICAL", second.health_state)
            self.assertEqual("URGENT", second.priority)

    def test_live_or_replay_evidence_never_creates_actionable_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            for mode in (RuntimeMode.LIVE_EQUIPMENT, RuntimeMode.REAL_REPLAY):
                evidence = critical_evidence(mode)
                with self.subTest(mode=mode):
                    self.assertIsNone(create_or_update_ticket(repository, evidence, deterministic_fallback(evidence, ())))
            self.assertEqual([], repository.list_tickets())

    def test_repository_query_limits_are_positive_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            for limit in (-1, 0, 1_001, True):
                with self.subTest(limit=limit), self.assertRaisesRegex(
                    ValueError, "Query limit"
                ):
                    repository.list_tickets(limit=limit)
                with self.subTest(prior_limit=limit), self.assertRaisesRegex(
                    ValueError, "Query limit"
                ):
                    repository.prior_context("TEST-WS-01", limit=limit)

    def test_repository_revision_changes_before_write_lock_is_released(self) -> None:
        class PausingLock:
            def __init__(self) -> None:
                self.lock = threading.RLock()
                self.released = threading.Event()
                self.proceed = threading.Event()

            def __enter__(self):
                self.lock.acquire()
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                self.lock.release()
                self.released.set()
                self.proceed.wait(timeout=5)

        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            lock = PausingLock()
            repository._lock = lock
            payload = {
                "ticket_id": "T-1",
                "machine_id": "TEST-WS-01",
                "status": "OPEN",
                "priority": "HIGH",
                "created_utc": NOW.isoformat(),
                "updated_utc": NOW.isoformat(),
            }
            worker = threading.Thread(target=repository.save, args=(payload,))
            worker.start()
            self.assertTrue(lock.released.wait(timeout=5))
            self.assertEqual(1, repository.revision)
            lock.proceed.set()
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())


if __name__ == "__main__":
    unittest.main()
