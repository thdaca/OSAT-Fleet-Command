"""Child-process restart check used by POST05, not a second inference path."""
import json
from pathlib import Path
import sys
from dataclasses import asdict

from ....pre_steps.pre01_common.pre01_common import RuntimeMode
from ....steps.step07_machine_model.core.model_io import load_machine_model
from ....steps.step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository
from .onboarding import IDENTITY
from .operational import make_pipeline, monitoring_run


def restart_probe(workspace):
    expected = json.loads((workspace / "reload-expectations.json").read_text(encoding="utf-8"))
    loaded = load_machine_model(workspace / "ws01-machine-model.json", active_machine=IDENTITY,
                                runtime_mode=RuntimeMode.SIMULATION, **expected)
    repository = MaintenanceRepository(workspace / "tickets.sqlite")
    ticket_before = repository.active_for_machine(IDENTITY.machine_id)
    pipeline = make_pipeline(repository, loaded.model)

    def tick(machine, checkpoint, *, force=False):
        machine.tick()

    monitoring_run(pipeline, tick)
    ticket = repository.active_for_machine(IDENTITY.machine_id)
    return {"new_process": True, "artifact_sha256": loaded.artifact_sha256,
            "ticket_before": ticket_before, "ticket_id": ticket["ticket_id"],
            "ticket_count": len(repository.list_tickets()), "health": pipeline.last_result.assessment.health_state.value,
            "priority": ticket["priority"], "status": ticket["status"],
            "step07_deviations": [asdict(d) for s in pipeline.last_result.assessment.subsystem_health for d in s.deviations]}


if __name__ == "__main__":
    print(json.dumps(restart_probe(Path(sys.argv[1])), sort_keys=True))
