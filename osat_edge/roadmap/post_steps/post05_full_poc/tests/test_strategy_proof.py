"""Protect executed PoC boundaries and counterfactuals, not report declarations."""
from contextlib import ExitStack
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from osat_edge import pipeline as pipeline_module
from osat_edge.roadmap.pre_steps.pre01_common.contracts import DataOrigin, HealthState
from osat_edge.roadmap.post_steps.post01_demo.demo import SyntheticTelemetrySource
from osat_edge.roadmap.post_steps.post05_full_poc.scenarios import onboarding, operational
from osat_edge.roadmap.post_steps.post05_full_poc.trace import decision_trace
from osat_edge.roadmap.steps.step11a_maintenance_db.repository import MaintenanceRepository


class StrategyProofTests(unittest.TestCase):
    def test_nominal_fit_has_no_future_fault_label_ticket_or_external_inputs(self):
        source = SyntheticTelemetrySource(onboarding.IDENTITY, onboarding.STATION)
        original_poll = source.poll
        events = []

        def nominal_poll():
            self.assertIsNone(source.injected_subsystem)
            self.assertEqual(0, source.injection_strength)
            return original_poll()

        def calibrate(*args, **kwargs):
            events.append(("calibrate", source.elapsed))
            cutoff = (source.started_at.timestamp() + source.elapsed)
            self.assertTrue(all(np.max(window.timestamps) <= cutoff for window in args[2].values()))
            return original_calibrate(*args, **kwargs)

        def fit(history, **kwargs):
            events.append(("fit", source.elapsed))
            return original_fit(history, **kwargs)

        def features(identity, station, windows, **kwargs):
            cutoff = kwargs["timestamp"].timestamp()
            self.assertTrue(all(np.max(w.timestamps) <= cutoff for w in windows.values()))
            return original_features(identity, station, windows, **kwargs)

        original_calibrate = onboarding.fit_relation_parameters
        original_fit = onboarding.fit_machine_model
        original_features = onboarding.extract_physical_features
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.object(source, "poll", side_effect=nominal_poll))
            stack.enter_context(patch.object(onboarding, "SyntheticTelemetrySource", return_value=source))
            calibration = stack.enter_context(patch.object(onboarding, "fit_relation_parameters", side_effect=calibrate))
            fitting = stack.enter_context(patch.object(onboarding, "fit_machine_model", side_effect=fit))
            validation = stack.enter_context(patch.object(onboarding, "evaluate_machine_model", wraps=onboarding.evaluate_machine_model))
            quality = stack.enter_context(patch.object(onboarding, "assess_telemetry", wraps=onboarding.assess_telemetry))
            stack.enter_context(patch.object(onboarding, "extract_physical_features", side_effect=features))
            # These downstream/research paths have no place in nominal fitting.
            for target in (
                "osat_edge.pipeline.MachinePipeline.tick",
                "osat_edge.roadmap.steps.step15_maintenance_ticket.tickets.create_or_update_ticket",
                "osat_edge.roadmap.steps.step05_family_model.model.fit_family_model",
                "osat_edge.roadmap.post_steps.post04_real_data_evaluation.evaluation.evaluate_all_real_data",
                "osat_edge.roadmap.post_steps.post04_real_data_evaluation.evaluation.evaluate_real_dataset",
            ):
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            loaded, _, record = onboarding.onboard(Path(directory))
            lineage = json.loads((Path(directory) / "onboarding-lineage.json").read_bytes())

        self.assertEqual([("calibrate", 130), ("fit", 165)], events)
        self.assertEqual(1, fitting.call_count)
        self.assertEqual(1, calibration.call_count)
        self.assertEqual(71, quality.call_count)
        history = fitting.call_args.args[0]
        self.assertIs(history.origin, DataOrigin.SYNTHETIC)
        self.assertEqual(35, len(history.healthy_feature_sets()))
        self.assertEqual(70, validation.call_count)  # holdout, then loaded-model holdout
        held_out = [call.args[2] for call in validation.call_args_list[:35]]
        self.assertGreater(min(row.window_start for row in held_out),
                           max(row.window_end for row in history.feature_sets))
        self.assertFalse({id(row) for row in held_out} & {id(row) for row in history.feature_sets})
        expected_features = {
            f"{channel.name}.{statistic}"
            for channel in onboarding.STATION.channels
            for statistic in ("median", "mad", "robust_slope_per_second")
        } | {"spindle.electromechanical_load_residual_a.median"}
        self.assertEqual(expected_features, set(history.feature_sets[0].by_name))
        self.assertEqual(261, len(lineage["batches"]))
        self.assertTrue(all(call.args[0] is loaded.model for call in validation.call_args_list[35:]))
        self.assertFalse(record["external_training_data_used"])

    def test_changing_only_future_validation_rejects_acceptance_without_changing_fit(self):
        class ChangedHoldout(SyntheticTelemetrySource):
            def poll(self):
                batch = super().poll()
                if self.elapsed > 226:
                    batch = replace(batch, samples=tuple(
                        replace(sample, value=sample.value + 1.0)
                        if sample.channel == "spindle_current" else sample
                        for sample in batch.samples))
                return batch

        original_fit = onboarding.fit_machine_model
        fitted = []

        def capture_fit(*args, **kwargs):
            model = original_fit(*args, **kwargs)
            fitted.append(model)
            return model

        with tempfile.TemporaryDirectory() as directory:
            nominal, _, _ = onboarding.onboard(Path(directory))
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(onboarding, "SyntheticTelemetrySource", ChangedHoldout), \
             patch.object(onboarding, "fit_machine_model", side_effect=capture_fit):
            with self.assertRaisesRegex(ValueError, "Separate PoC nominal validation failed"):
                onboarding.onboard(Path(directory))
            self.assertFalse((Path(directory) / "ws01-machine-model.json").exists())
        self.assertEqual(1, len(fitted))
        self.assertEqual(nominal.model.physics_parameters, fitted[0].physics_parameters)
        for state, context in nominal.model.contexts.items():
            np.testing.assert_array_equal(context.center, fitted[0].contexts[state].center)
            np.testing.assert_array_equal(context.scale, fitted[0].contexts[state].scale)

    def test_loaded_model_and_actual_physics_fault_ticket_paths_drive_monitoring(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            loaded, _, _ = onboarding.onboard(workspace)
            repository = MaintenanceRepository(workspace / "tickets.sqlite")
            machine = operational.make_pipeline(repository, loaded.model)
            # A test-only counterfactual baseline: identical telemetry/physics,
            # much larger robust scales. It is never saved or accepted for use.
            counterfactual = replace(loaded.model, contexts={
                state: replace(context, scale=context.scale * 1_000_000)
                for state, context in loaded.model.contexts.items()})
            other = operational.make_pipeline(MaintenanceRepository(workspace / "counterfactual.sqlite"), counterfactual)
            transitions = []
            actions = []
            actual_faults = []
            original_fault = pipeline_module.build_fault_evidence

            def fault_from_step10(assessment):
                evidence = original_fault(assessment)
                actual_faults.append(evidence)
                return evidence

            def tick(machine, checkpoint, *, force=False):
                previous = machine.last_result.assessment.health_state.value if machine.last_result else "UNKNOWN"
                prior = repository.active_for_machine(onboarding.IDENTITY.machine_id)
                result = machine.tick()
                self.assertIs(result.fault_evidence, actual_faults[-1])
                if result.assessment.transitioned:
                    transitions.append(result.assessment.health_state.value)
                trace = decision_trace(checkpoint, machine, result, previous, loaded.artifact_sha256, prior)
                if trace["ticket_action"] in {"CREATED", "ESCALATED_SAME_TICKET"}:
                    actions.append(trace)
                if result.assessment.health_state in {HealthState.UNKNOWN, HealthState.NORMAL, HealthState.WATCH}:
                    self.assertIsNone(prior)
                    self.assertIsNone(result.ticket)

            with patch.object(pipeline_module, "evaluate_machine_model", wraps=pipeline_module.evaluate_machine_model) as scoring, \
                 patch.object(pipeline_module, "calculate_physical_residuals", wraps=pipeline_module.calculate_physical_residuals) as physics, \
                 patch.object(pipeline_module, "build_fault_evidence", side_effect=fault_from_step10), \
                 patch.object(pipeline_module, "create_or_update_ticket", wraps=pipeline_module.create_or_update_ticket) as tickets:
                operational.monitoring_run(machine, tick)
                self.assertTrue(scoring.call_count > 150)
                self.assertEqual(scoring.call_count, physics.call_count)
                self.assertTrue(all(call.args[0] is loaded.model for call in scoring.call_args_list))
                self.assertTrue(all(call.kwargs["fitted_parameters"] is loaded.model.physics_parameters for call in physics.call_args_list))
                self.assertEqual(2, tickets.call_count)
                self.assertTrue(all(call.args[1] in actual_faults for call in tickets.call_args_list))

            operational.monitoring_run(other, lambda machine, *args, **kwargs: machine.tick())
            self.assertEqual(machine.last_result.feature_set, other.last_result.feature_set)
            self.assertEqual("CRITICAL", machine.last_result.assessment.health_state.value)
            self.assertEqual("NORMAL", other.last_result.assessment.health_state.value)
            self.assertEqual(["NORMAL", "WATCH", "DEGRADED", "CRITICAL"], transitions)
            self.assertEqual(["CREATED", "ESCALATED_SAME_TICKET"], [trace["ticket_action"] for trace in actions])
            self.assertEqual(1, len(repository.list_tickets()))
            self.assertEqual(actions[0]["ticket"]["ticket_id"], actions[1]["ticket"]["ticket_id"])
            result = machine.last_result
            trace = decision_trace("proof", machine, result, "CRITICAL", loaded.artifact_sha256,
                                   repository.active_for_machine(onboarding.IDENTITY.machine_id))
            self.assertEqual([asdict(feature) for feature in result.feature_set.features if feature.kind == "physics"], trace["physics"])
            self.assertEqual(("spindle",), result.fault_evidence.suspected_subsystems)
            self.assertIn("poc-ws01-spindle-review", str(machine.manual_chunks))

    def test_restart_qualification_compares_replayed_health_and_model_identity(self):
        original_run = subprocess.run

        def changed_restart(*args, **kwargs):
            result = original_run(*args, **kwargs)
            record = json.loads(result.stdout)
            record[changed_field] = changed_value
            return subprocess.CompletedProcess(
                result.args, result.returncode, json.dumps(record), result.stderr)

        for changed_field, changed_value in (("health", "NORMAL"), ("artifact_sha256", "different-model")):
            with self.subTest(field=changed_field), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                loaded, expected, _ = onboarding.onboard(workspace)
                with patch.object(operational.subprocess, "run", side_effect=changed_restart):
                    report, _ = operational.run_operational(workspace, loaded, expected)
                self.assertEqual("FAIL", report["outcomes"]["process_restart_model_ticket_reload"])
