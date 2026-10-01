"""POST05 public orchestration: existing PRE/STEP decisions, new proof only."""
from pathlib import Path
import tempfile

from ...steps.step07_machine_model.model_io import canonical_bytes
from ...steps.step11a_maintenance_db.repository import MaintenanceRepository
from .lineage import PROJECT_ROOT, COMMITTED_POC_PATH
from .reporting import assemble_report, poc_summary
from .scenarios.onboarding import onboard
from .scenarios.operational import run_operational
from .scenarios.enrichment import run_enrichment
from .scenarios.connectivity import run_connectivity

__all__ = ["run_full_poc", "write_poc_report", "poc_summary", "COMMITTED_POC_PATH"]


def run_full_poc(*, artifact_root: Path | None = None):
    """Run once in a fresh ignored workspace; no state leaks between runs.

    Supplying an artifact_root keeps that run's model/SQLite/lineage for manual
    inspection. It must still be under .artifacts; never overwrite source files.
    """
    generated = (PROJECT_ROOT / ".artifacts").resolve()
    generated.mkdir(exist_ok=True)
    if artifact_root is None:
        with tempfile.TemporaryDirectory(prefix="poc-", dir=generated) as directory:
            return _run(Path(directory))
    root = Path(artifact_root).resolve()
    if not root.is_relative_to(generated) or root == generated:
        raise ValueError("PoC runtime artifacts require a new subdirectory of .artifacts")
    root.mkdir(parents=True, exist_ok=False)
    return _run(root)


def _run(workspace):
    loaded, expected, onboarding = onboard(workspace)
    operational, critical = run_operational(workspace, loaded, expected)
    enrichment = run_enrichment(critical, MaintenanceRepository(workspace / "tickets.sqlite"))
    connectivity = run_connectivity(workspace)
    return assemble_report(onboarding, operational, enrichment, connectivity)


def write_poc_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(report))
    return path
