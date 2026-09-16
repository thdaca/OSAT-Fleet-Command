"""Persistence is exact and fail-closed without changing Step07 arithmetic."""
from dataclasses import replace
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import DataOrigin, EquipmentState, MachineIdentity, RuntimeMode
from osat_edge.roadmap.steps.step02_physical_features.step02_physical_features import Feature, FeatureSet
from osat_edge.roadmap.steps.step07_machine_model.step07_machine_model import ContextModel, MachineModel, evaluate_machine_model
from osat_edge.roadmap.steps.step07_machine_model.core.model_io import (
    MachineModelArtifactError, VALIDATION_STATUS, canonical_bytes, feature_contract,
    identity_sha256, physics_identity, save_machine_model, load_machine_model,
)


class MachineModelPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "model.json"
        self.machine = MachineIdentity("IO-WS", "wafer_saw", "WS-01", "Artifact test")
        context = ContextModel(EquipmentState.PROCESSING, ("current",), ("spindle",), ("location",),
                               np.array([1.23456789012345]), np.array([0.000123456789]))
        self.model = MachineModel(self.machine, DataOrigin.SYNTHETIC, {EquipmentState.PROCESSING: context}, {"fit": {"a": 1.25}})
        self.save = dict(source_sha256="a" * 64, calibration_sha256="b" * 64,
                         validation_sha256="c" * 64, validation_status=VALIDATION_STATUS)
        self.expected = dict(active_machine=self.machine, runtime_mode=RuntimeMode.SIMULATION,
                             expected_feature_contract=feature_contract(self.model), expected_physics_sha256=physics_identity(self.model),
                             expected_source_sha256="a" * 64, expected_calibration_sha256="b" * 64,
                             expected_validation_sha256="c" * 64)
        self.digest = save_machine_model(self.model, self.path, **self.save)

    def mutate(self, edit, *, resign=True):
        envelope = json.loads(self.path.read_bytes())
        edit(envelope["payload"])
        if resign:
            envelope["artifact_sha256"] = identity_sha256(envelope["payload"])
        self.path.write_bytes(canonical_bytes(envelope))

    def test_save_load_exactly_preserves_step07_outputs(self):
        loaded = load_machine_model(self.path, **self.expected)
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        features = FeatureSet(self.machine, now, EquipmentState.PROCESSING, now, now,
                              (Feature("current", 1.2356789, "spindle", "location"),))
        self.assertEqual(evaluate_machine_model(self.model, self.machine, features, runtime_mode=RuntimeMode.SIMULATION),
                         evaluate_machine_model(loaded.model, self.machine, features, runtime_mode=RuntimeMode.SIMULATION))
        self.assertEqual(self.digest, loaded.artifact_sha256)

    def test_deterministic_bytes_and_readonly_parameters(self):
        original = self.path.read_bytes()
        self.assertEqual(self.digest, save_machine_model(self.model, self.path, **self.save))
        self.assertEqual(original, self.path.read_bytes())
        self.assertFalse(load_machine_model(self.path, **self.expected).model.contexts[EquipmentState.PROCESSING].center.flags.writeable)

    def test_corruption_and_missing_files_rejected(self):
        self.mutate(lambda p: p.update(source_sha256="d" * 64), resign=False)
        with self.assertRaises(MachineModelArtifactError):
            load_machine_model(self.path, **self.expected)
        with self.assertRaises(MachineModelArtifactError):
            load_machine_model(self.path.with_name("absent.json"), **self.expected)

    def test_wrong_machine_family_station_rejected_even_with_valid_hash(self):
        for field, wrong in (("machine_id", "OTHER"), ("family", "wire_bond"), ("station_id", "WB-04")):
            with self.subTest(field=field), self.assertRaises(MachineModelArtifactError):
                load_machine_model(self.path, **{**self.expected, "active_machine": replace(self.machine, **{field: wrong})})

    def test_schema_software_validation_contract_and_source_rejected(self):
        original = self.path.read_bytes()
        for field, value in (("schema_version", "V0"), ("software_version", "0.2.5"),
                             ("validation_status", "NOT_VALIDATED"), ("feature_contract", {}),
                             ("source_sha256", "e" * 64), ("physics_sha256", "f" * 64),
                             ("calibration_sha256", "d" * 64), ("validation_sha256", "e" * 64)):
            self.path.write_bytes(original)
            self.mutate(lambda p: p.update({field: value}))
            with self.subTest(field=field), self.assertRaises(MachineModelArtifactError):
                load_machine_model(self.path, **self.expected)

    def test_negative_zero_boolean_and_nonfinite_parameters_rejected(self):
        original = self.path.read_bytes()
        for value in (-1, 0, True, "1"):
            self.path.write_bytes(original)
            self.mutate(lambda p: p["contexts"]["PROCESSING"].update(scale=[value]))
            with self.subTest(value=value), self.assertRaises(MachineModelArtifactError):
                load_machine_model(self.path, **self.expected)
        self.path.write_bytes(b'{"payload":NaN,"artifact_sha256":"x"}')
        with self.assertRaises(MachineModelArtifactError):
            load_machine_model(self.path, **self.expected)

    def test_duplicate_keys_rejected(self):
        self.path.write_bytes(b'{"payload":{},"payload":{},"artifact_sha256":"x"}')
        with self.assertRaises(MachineModelArtifactError):
            load_machine_model(self.path, **self.expected)

    def test_synthetic_cannot_load_for_live_or_replay(self):
        for mode in (RuntimeMode.LIVE_EQUIPMENT, RuntimeMode.REAL_REPLAY):
            with self.subTest(mode=mode), self.assertRaises(MachineModelArtifactError):
                load_machine_model(self.path, **{**self.expected, "runtime_mode": mode})

    def test_external_benchmark_cannot_be_operational_model(self):
        self.mutate(lambda p: p.update(origin="EXTERNAL_BENCHMARK"))
        with self.assertRaises(MachineModelArtifactError):
            load_machine_model(self.path, **self.expected)

    def test_failed_save_preserves_original_and_removes_temporary(self):
        before = self.path.read_bytes()
        with self.assertRaises(MachineModelArtifactError):
            save_machine_model(self.model, self.path, **{**self.save, "validation_status": "REJECTED"})
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([self.path], list(self.path.parent.iterdir()))
