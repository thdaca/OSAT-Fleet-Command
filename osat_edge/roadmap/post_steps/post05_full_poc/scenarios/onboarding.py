"""WS-01 synthetic nominal collection, calibration, fit and disjoint validation."""
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ....pre_steps.pre01_common.contracts import DataOrigin, EquipmentState, MachineIdentity, RuntimeMode
from ....pre_steps.pre02_machine_registry.registry import STATIONS
from ....steps.step01_physics_library.library import relations_for_family
from ....steps.step02_physical_features.features import extract_physical_features
from ....steps.step03_physical_residuals.residuals import calculate_physical_residuals, fit_relation_parameters
from ....steps.step06_machine_history.history import HealthyInterval, MachineHistory
from ....steps.step07_machine_model.model import fit_machine_model, evaluate_machine_model
from ....steps.step07_machine_model.model_io import (
    VALIDATION_STATUS, canonical_bytes, identity_sha256, feature_contract, physics_identity,
    save_machine_model, load_machine_model,
)
from ....steps.step08_live_telemetry.store import BoundedTelemetryStore, FEATURE_WINDOW, assess_telemetry
from ....steps.step09_health_risk.health import WATCH_ENTRY
from ...post01_demo.demo import SyntheticTelemetrySource, DEMO_START

STATION = STATIONS["wafer_saw"]
IDENTITY = MachineIdentity("POC-WS-01", STATION.family, STATION.station_id, STATION.name)
NOMINAL_DESIGNATION = "POC_DESIGNATED_NOMINAL_SYNTHETIC_NOT_INDEPENDENT_PLANT_HEALTH"


def batch_record(batch):
    return {
        "samples": [{**asdict(s), "timestamp": s.timestamp.isoformat()} for s in batch.samples],
        "context": {**asdict(batch.context), "timestamp": batch.context.timestamp.isoformat()},
    }


def onboard(workspace: Path):
    source = SyntheticTelemetrySource(IDENTITY, STATION)
    store = BoundedTelemetryStore(IDENTITY, STATION)
    batches = []

    def ingest():
        batch = source.poll()
        store.append_batch(batch)
        batches.append(batch_record(batch))
        return batch.context.timestamp

    for _ in range(130):
        now = ingest()
    channels = [channel.name for channel in STATION.channels]
    windows = store.windows(channels, end=now)
    if not assess_telemetry(store, now=now, windows=windows).observable:
        raise ValueError("PoC nominal calibration telemetry was not observable")
    calibration_sha = identity_sha256(batches)
    parameters = {
        relation.relation_id: fit_relation_parameters(STATION.family, relation.relation_id, windows)
        for relation in relations_for_family(STATION.family) if relation.fit is not None
    }

    def row():
        now = ingest()
        windows = store.windows(channels, end=now)
        status = assess_telemetry(store, now=now, windows=windows)
        if not status.valid or not status.observable:
            raise ValueError("PoC nominal history is invalid/unobservable")
        features = extract_physical_features(IDENTITY, STATION, windows, timestamp=now,
                                            equipment_state=EquipmentState.PROCESSING,
                                            window_start=now - FEATURE_WINDOW)
        residuals = calculate_physical_residuals(STATION.family, windows, fitted_parameters=parameters)
        return replace(features, features=features.features + residuals)

    training = tuple(row() for _ in range(35))
    source_sha = identity_sha256(batches)
    history = MachineHistory(IDENTITY, DataOrigin.SYNTHETIC, training, (
        HealthyInterval(IDENTITY.machine_id, DEMO_START, training[-1].window_end),
    ))
    model = fit_machine_model(history, physics_parameters=parameters, minimum_rows_per_state=20)
    # Purge the whole feature-window span before validation. No shared samples.
    validation_start = len(batches)
    for _ in range(61):
        ingest()
    validation = tuple(row() for _ in range(35))
    evaluated = [evaluate_machine_model(model, IDENTITY, item,
                                      runtime_mode=RuntimeMode.SIMULATION) for item in validation]
    accepted = all(result.available and all(d.score < WATCH_ENTRY for d in result.deviations
                                           if d.kind in {"location", "physics"}) for result in evaluated)
    if not accepted or validation[0].window_start <= training[-1].window_end:
        raise ValueError("Separate PoC nominal validation failed")
    validation_sha = identity_sha256(batches[validation_start:])
    path = workspace / "ws01-machine-model.json"
    artifact_sha = save_machine_model(model, path, source_sha256=source_sha,
                                     calibration_sha256=calibration_sha, validation_sha256=validation_sha,
                                     validation_status=VALIDATION_STATUS)
    load_options = dict(active_machine=IDENTITY, runtime_mode=RuntimeMode.SIMULATION,
                        expected_feature_contract=feature_contract(model), expected_physics_sha256=physics_identity(model),
                        expected_source_sha256=source_sha, expected_calibration_sha256=calibration_sha,
                        expected_validation_sha256=validation_sha)
    loaded = load_machine_model(path, **load_options)
    reloaded = [evaluate_machine_model(loaded.model, IDENTITY, item,
                                     runtime_mode=RuntimeMode.SIMULATION) for item in validation]
    exact = evaluated == reloaded
    if not exact:
        raise ValueError("Model round-trip changed Step07 output")
    record = {
        "status": "PASS", "designation": NOMINAL_DESIGNATION, "origin": DataOrigin.SYNTHETIC.value,
        "independently_confirmed_plant_health": False, "source_sha256": source_sha,
        "calibration_sha256": calibration_sha, "validation_sha256": validation_sha,
        "physics_sha256": physics_identity(model), "artifact_sha256": artifact_sha,
        "validation_status": VALIDATION_STATUS, "training_rows": len(training),
        "validation_rows": len(validation), "training_end": training[-1].window_end.isoformat(),
        "validation_window_start": validation[0].window_start.isoformat(),
        "disjoint_validation_windows": True, "save_load_step07_exact": exact,
        "physics_parameters": parameters, "feature_contract": feature_contract(model),
        "validation_outputs_sha256": identity_sha256([asdict(item) for item in evaluated]),
        "external_training_data_used": False,
    }
    (workspace / "onboarding-lineage.json").write_bytes(canonical_bytes({
        "designation": NOMINAL_DESIGNATION, "origin": "SYNTHETIC", "batches": batches,
        "record": record,
    }))
    return loaded, load_options, record
