import builtins
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from osat_edge.roadmap.pre_steps.pre01_common.core.authority import SHADOW_FORBIDDEN, require_shadow_permission
from osat_edge.roadmap.post_steps.post05_full_poc.post05_full_poc import run_full_poc, COMMITTED_POC_PATH
from osat_edge.roadmap.post_steps.post05_full_poc.core.reporting import PROJECT_ROOT, frozen_lineage
from osat_edge.roadmap.steps.step07_machine_model.core.model_io import identity_sha256

HAS_SIMULATOR = importlib.util.find_spec("secsgem") is not None


class FullPocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_full_poc()
        cls.outcomes = cls.report["scenarios"]
        cls.trace = cls.report["decision_trace"]

    def test_one_command_runs_complete_poc_without_pyqt_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "poc.json"
            command = [sys.executable, "-W", "error", "-m", "osat_edge.ui.cli", "poc", "--output", str(output)]
            if HAS_SIMULATOR:
                command.append("--require-connectivity")
            result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(self.report, json.loads(output.read_bytes()))
            self.assertIn("SHADOW / READ-ONLY", result.stdout)

    def test_repeat_run_without_llm_family_training_or_external_loading_is_identical(self):
        original_import = builtins.__import__

        def no_research_runtime(name, *args, **kwargs):
            if name.split(".")[0] in {"llama_cpp", "pint", "sympy", "pydoe"}:
                raise ImportError("Optional research/LLM package intentionally unavailable")
            return original_import(name, *args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(patch("builtins.__import__", side_effect=no_research_runtime))
            for target in (
                "osat_edge.roadmap.steps.step05_family_model.step05_family_model.fit_family_model",
                "osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation.evaluate_all_real_data",
            ):
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            self.assertEqual(self.report, run_full_poc())

    def test_report_digest_and_committed_record(self):
        unsigned = dict(self.report)
        digest = unsigned.pop("report_sha256")
        self.assertEqual(identity_sha256(unsigned), digest)
        committed = json.loads(COMMITTED_POC_PATH.read_bytes())
        if HAS_SIMULATOR:
            self.assertEqual(committed, self.report)
        else:
            current = dict(self.report)
            for value in (current, committed):
                value.pop("report_sha256")
                value.pop("qualification")
                value.pop("connectivity")
                value["components"] = {k: v for k, v in value["components"].items() if k != "connectivity_simulation"}
            self.assertEqual(committed, current)

    def test_cold_start_unknown_despite_valid_telemetry(self):
        trace = [t for t in self.trace if t["checkpoint"] == "cold_start"][-1]
        self.assertEqual("UNKNOWN", trace["health"])
        self.assertEqual("VALID", trace["telemetry"]["state"])
        self.assertTrue(trace["telemetry"]["observable"])
        self.assertIsNone(trace["exact_machine_model_artifact_sha256"])

    def test_onboarding_is_disjoint_synthetic_and_separately_accepted(self):
        onboard = self.report["onboarding"]
        self.assertEqual("ACCEPTED_RESEARCH_ONLY", onboard["validation_status"])
        self.assertEqual("SYNTHETIC", onboard["origin"])
        self.assertFalse(onboard["independently_confirmed_plant_health"])
        self.assertGreater(onboard["validation_window_start"], onboard["training_end"])
        self.assertEqual(35, onboard["training_rows"])
        self.assertEqual(35, onboard["validation_rows"])
        self.assertTrue(onboard["save_load_step07_exact"])

    def test_healthy_nominal_operation_and_frozen_progression(self):
        self.assertEqual("NORMAL", self.outcomes["healthy_operation"])
        self.assertEqual(["NORMAL", "WATCH", "DEGRADED", "CRITICAL"], self.report["health_progression"])
        self.assertEqual(["CRITICAL", "DEGRADED", "WATCH", "NORMAL"], self.report["recovery_progression"])

    def test_physics_and_step07_evidence_are_linked_to_spindle(self):
        elevated = [t for t in self.trace if t["checkpoint"] == "progressive_spindle" and t["fault_evidence"]]
        self.assertTrue(elevated)
        for trace in elevated:
            self.assertEqual(["spindle"], trace["fault_evidence"]["suspected_subsystems"])
            self.assertTrue(trace["physics"])
            self.assertTrue(all(f["relation_id"] for f in trace["physics"]))
            self.assertTrue(any(d["kind"] == "physics" and d["score"] > 0 for d in trace["step07_deviations"]))
            self.assertEqual(self.report["onboarding"]["artifact_sha256"], trace["exact_machine_model_artifact_sha256"])
            self.assertIsNone(trace["advisory_family_risk"])

    def test_context_shift_has_no_spurious_fault(self):
        trace = next(t for t in self.trace if t["checkpoint"] == "legitimate_context_shift")
        self.assertEqual("IDLE", trace["context"])
        self.assertEqual("UNKNOWN", trace["health"])
        self.assertIsNone(trace["fault_evidence"])
        self.assertIn("No healthy model", trace["transition_reason"])

    def test_missing_stale_disconnect_are_unknown_not_cached_normal(self):
        self.assertEqual("UNKNOWN", self.outcomes["missing_required_signal"])
        self.assertEqual("UNKNOWN", self.outcomes["stale_telemetry"])
        self.assertEqual({"last_known_health": "NORMAL", "current_health": "UNKNOWN", "connection": "DISCONNECTED"},
                         self.outcomes["connectivity_loss"])

    def test_malformed_batch_is_atomic_invalid_unknown_and_alive(self):
        self.assertEqual({"health": "UNKNOWN", "telemetry": "INVALID", "store_unchanged": True, "runtime_alive": True},
                         self.outcomes["malformed_atomic_batch"])

    def test_corrupt_model_is_rejected_and_unknown(self):
        self.assertEqual({"rejected": True, "health": "UNKNOWN"}, self.outcomes["corrupted_machine_model"])

    def test_one_demo_ticket_created_escalated_persisted_and_not_closed(self):
        self.assertEqual(1, len(self.report["tickets"]))
        ticket = self.report["tickets"][0]
        self.assertEqual("OPEN", ticket["status"])
        self.assertEqual("URGENT", ticket["priority"])
        self.assertTrue(ticket["demo_only"])
        self.assertEqual("POC-WS-01", ticket["machine_id"])
        self.assertEqual(["spindle"], ticket["suspected_subsystems"])
        actions = [t for t in self.trace if t["ticket_action"] in {"CREATED", "ESCALATED_SAME_TICKET"}]
        self.assertEqual(["CREATED", "ESCALATED_SAME_TICKET"], [t["ticket_action"] for t in actions])
        self.assertEqual(["HIGH", "URGENT"], [t["ticket"]["priority"] for t in actions])
        self.assertEqual({ticket["ticket_id"]}, {t["ticket"]["ticket_id"] for t in actions})

    def test_real_process_restart_reloads_model_and_ticket(self):
        restart = self.report["restart"]
        self.assertTrue(restart["new_process"])
        self.assertTrue(restart["step07_outputs_identical"])
        self.assertTrue(restart["ticket_loaded_exactly"])
        self.assertEqual(1, restart["ticket_count"])

    def test_retrieval_schema_validation_and_no_llm_fallback(self):
        result = self.report["enrichment"]
        self.assertEqual(["poc-ws01-spindle-review"], result["retrieved_source_ids"])
        for key in ("ticket_existed_before_retrieval", "invalid_authority_fields_rejected", "ticket_unchanged_by_schema_checks"):
            self.assertTrue(result[key])
        self.assertEqual("NOT_CONFIGURED", result["llm_execution"])
        self.assertEqual("deterministic-fallback", result["fallback_backend"])

    @unittest.skipUnless(HAS_SIMULATOR, "optional secsgem simulator not installed")
    def test_loopback_hsms_receives_only_approved_data_and_disconnects_safely(self):
        result = self.report["connectivity"]
        self.assertEqual("PASS", result["status"])
        self.assertEqual("SYNTHETIC", result["DataOrigin"])
        for field in ("unmapped_signals_rejected", "malformed_values_rejected", "rejected_reports_store_unchanged",
                      "rejected_reports_telemetry_invalid", "session_loss_detected"):
            self.assertTrue(result[field])
        self.assertEqual("UNKNOWN", result["current_health_after_loss"])
        self.assertEqual("INVALID", result["telemetry_after_loss"])
        self.assertEqual(["S6F12", "SELECT_RSP"], result["sent_by_fleet_command"])
        self.assertEqual(0, result["equipment_control_messages"])
        self.assertEqual(0, result["operational_ticket_count"])

    def test_missing_simulator_is_explicitly_not_qualified(self):
        from osat_edge.roadmap.post_steps.post05_full_poc.scenarios.connectivity import run_connectivity
        original = builtins.__import__
        def without_secsgem(name, *args, **kwargs):
            if name.startswith("secsgem"):
                raise ImportError("optional dependency absent")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=without_secsgem):
            result = run_connectivity(Path("unused"))
        self.assertEqual("NOT_RUN_OPTIONAL_DEPENDENCY_ABSENT", result["status"])

    def test_shadow_is_fail_closed_and_not_live_ticket_authority(self):
        for action in (*SHADOW_FORBIDDEN, "unknown_action"):
            with self.subTest(action=action), self.assertRaises(PermissionError):
                require_shadow_permission(action)
        self.assertFalse(self.report["authority"]["live_equipment_tickets"])
        for flag in ("REAL_OSAT_VALIDATED", "PROSPECTIVE_PLANT_VALIDATED", "PRODUCTION_QUALIFIED"):
            self.assertFalse(self.report[flag])

    def test_all_frozen_science_and_external_result_bytes_are_unchanged(self):
        self.assertEqual("PASS", frozen_lineage()["status"])
        self.assertFalse(self.report["evidence_lineage"]["external_data_used_for_operational_model"])
        self.assertEqual("4148cccf463e8806b2748715f7bd68784941121fc0157a3cc113f47ba8a4be2f",
                         self.report["evidence_lineage"]["external_evidence_artifact_sha256"])
        from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.evidence_lifecycle import evaluator_source_sha256
        pin = json.loads((PROJECT_ROOT / "osat_edge/roadmap/post_steps/post04_real_data_evaluation/resources/0.2.6-reproducer.json").read_bytes())
        self.assertEqual(evaluator_source_sha256(), pin["evaluator_sha256"])

    def test_runtime_output_cannot_be_written_over_source_tree(self):
        with self.assertRaises(ValueError):
            run_full_poc(artifact_root=PROJECT_ROOT / "osat_edge")

    def test_frozen_external_verifier_rejects_unapproved_source_drift(self):
        from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core import evidence_lifecycle as lifecycle
        frozen = json.loads(lifecycle.CURRENT_EVIDENCE_PATH.read_bytes())
        report = {"summary": frozen["summary"], "datasets": frozen["results"]}
        with patch.object(lifecycle, "evaluator_source_sha256", return_value="0" * 64), \
             patch.object(lifecycle, "current_real_data_evidence_record", return_value=frozen), \
             patch.object(lifecycle, "deterministic_scientific_sha256", return_value=frozen["deterministic_comparison_report_sha256"]), \
             patch("osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation.evaluate_all_real_data", return_value=report):
            with self.assertRaisesRegex(lifecycle.RealDataEvaluationError, "approved frozen-experiment reproducer"):
                lifecycle.verify_committed_real_data_evidence(PROJECT_ROOT / "benchmarks/_external")
