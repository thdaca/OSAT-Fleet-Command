"""Roll-to-roll web-tension provenance and source-field inspection."""
from __future__ import annotations
import io
from pathlib import Path
import time
from typing import Any, Sequence
import zipfile
from xml.etree import ElementTree as ET
from ..core.dataset_context import MAXIMUM_GENERIC_MEMBERS, MAXIMUM_GENERIC_MEMBER_BYTES, MAXIMUM_GENERIC_TOTAL_BYTES, RealDataEvaluationError, _base_report, _unverified_input
from ..core.source_files import _zip_members
R2R_OFFICIAL_ARCHIVE_SHA256 = "3168a831e38c9388e73ba809661c282b560640ea269beba5d976340eb5e1ac16"
R2R_METADATA_LABEL_FIELDS = frozenset({"Date", "Model", "Trigger", "Film kind"})
R2R_CONTROLLER_CONFIGURATION_PREFIXES = (
    "OutFeeder-Control:",
    "ReWinder-Control:",
)
def _xlsx_first_row(content: bytes) -> tuple[str, ...]:
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as workbook:
            files = [item for item in workbook.infolist() if not item.is_dir()]
            if len(files) > MAXIMUM_GENERIC_MEMBERS:
                raise RealDataEvaluationError("XLSX contains too many members")
            if any(item.file_size > MAXIMUM_GENERIC_MEMBER_BYTES for item in files):
                raise RealDataEvaluationError("XLSX member exceeds the size limit")
            if sum(item.file_size for item in files) > MAXIMUM_GENERIC_TOTAL_BYTES:
                raise RealDataEvaluationError("XLSX expands beyond the size limit")

            shared: list[str] = []
            if "xl/sharedStrings.xml" in workbook.namelist():
                shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
                for item in shared_root.findall(f"{{{namespace}}}si"):
                    shared.append(
                        "".join(node.text or "" for node in item.iter(f"{{{namespace}}}t"))
                    )
            sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise RealDataEvaluationError("R2R workbook is invalid or lacks sheet1") from exc
    first_row = sheet.find(f".//{{{namespace}}}sheetData/{{{namespace}}}row")
    if first_row is None:
        raise RealDataEvaluationError("R2R workbook has no header row")
    values: list[str] = []
    for cell in first_row.findall(f"{{{namespace}}}c"):
        cell_type = cell.get("t")
        raw = cell.find(f"{{{namespace}}}v")
        value = "" if raw is None else raw.text or ""
        if cell_type == "s" and value:
            try:
                value = shared[int(value)]
            except (IndexError, ValueError) as exc:
                raise RealDataEvaluationError("R2R workbook has an invalid shared string") from exc
        elif cell_type == "inlineStr":
            value = "".join(
                node.text or "" for node in cell.iter(f"{{{namespace}}}t")
            )
        if value.strip():
            values.append(value.strip())
    return tuple(values)


def _classify_r2r_source_fields(
    fields: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    """Classify the pinned v2 sensor schema without counting metadata as signals.

    Date/model/trigger/material labels are metadata.  Named controller tuning
    fields are configuration.  Every other field in the checksum-pinned sensor
    schema is a physical-valued source field, whether or not Fleet Command has
    an exact canonical mapping for it.
    """

    classified: dict[str, list[str]] = {
        "physical_signal": [],
        "metadata_or_label": [],
        "controller_configuration": [],
    }
    for field in fields:
        if field in R2R_METADATA_LABEL_FIELDS:
            classified["metadata_or_label"].append(field)
        elif field.startswith(R2R_CONTROLLER_CONFIGURATION_PREFIXES):
            classified["controller_configuration"].append(field)
        else:
            classified["physical_signal"].append(field)
    return {name: tuple(values) for name, values in classified.items()}


def _r2r_source_field_coverage(
    fields: Sequence[str], mapped_sources: set[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    classified = _classify_r2r_source_fields(fields)
    physical_fields = classified["physical_signal"]
    if not mapped_sources.issubset(physical_fields):
        raise RealDataEvaluationError("R2R mapped fields must classify as physical source signals")
    mapped_count = len(mapped_sources)
    physical_count = len(physical_fields)
    if physical_count == 0:
        raise RealDataEvaluationError("R2R source schema has no physical signal fields")
    fraction = mapped_count / physical_count
    return (
        {"mapped": mapped_count, "total": physical_count, "fraction": fraction},
        {
            "exact_mapped_physical_signals": mapped_count,
            "physical_signal_fields": physical_count,
            "inspected_source_fields": len(fields),
            "metadata_or_label_fields_excluded": len(classified["metadata_or_label"]),
            "controller_configuration_fields_excluded": len(
                classified["controller_configuration"]
            ),
            "fraction": fraction,
            "classification_rule": (
                "For the checksum-pinned v2 sensor schema, Date/Model/Trigger/Film kind "
                "are metadata or labels; OutFeeder-Control:/ReWinder-Control: fields are "
                "controller configuration; all remaining physical-valued fields form "
                "the source-signal denominator."
            ),
        },
    )


def _evaluate_r2r(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, _content_hash, members = _zip_members(path)
    if source_hash != R2R_OFFICIAL_ARCHIVE_SHA256:
        return _unverified_input(
            "r2r-web-tension",
            source_hash,
            "The local artifact does not match the pinned public Mendeley Data v2 dataset.zip SHA-256.",
            files=len(members),
            expected_official_archive_sha256=R2R_OFFICIAL_ARCHIVE_SHA256,
        )
    aggregate = [
        content
        for name, content in members.items()
        if name.replace("\\", "/").endswith("dataset/dataset.xlsx")
    ]
    sensor_items = [
        (name, content)
        for name, content in members.items()
        if "/sensor_data/" in name.replace("\\", "/") and name.lower().endswith(".xlsx")
    ]
    if len(aggregate) != 1 or not sensor_items:
        raise RealDataEvaluationError("Official R2R archive lacks its aggregate or sensor workbooks")
    aggregate_header = _xlsx_first_row(aggregate[0])
    sensor_headers = {_xlsx_first_row(content) for _name, content in sensor_items}
    if len(sensor_headers) != 1:
        raise RealDataEvaluationError("R2R sensor workbooks do not share one source schema")
    sensor_header = next(iter(sensor_headers))
    mapped = (
        ("Film Tension #1 (kg)", "film_tension_1", "kg"),
        ("Film Tension #2 (kg)", "film_tension_2", "kg"),
        ("Film Tension #3 (kg)", "film_tension_3", "kg"),
        ("Web Current Speed (mm/sec)", "web_speed", "mm/sec"),
    )
    missing = sorted(source for source, _target, _unit in mapped if source not in sensor_header)
    if missing:
        raise RealDataEvaluationError(
            f"R2R exact physical source fields are missing: {', '.join(missing)}"
        )
    mapped_sources = {source for source, _target, _unit in mapped}
    channel_coverage, source_field_coverage = _r2r_source_field_coverage(
        sensor_header, mapped_sources
    )
    report = _base_report(
        "r2r-web-tension",
        source_hash,
        provenance_verified=True,
        provenance_method="pinned public Mendeley Data v2 dataset.zip SHA-256",
    )
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "official_version": "2",
            "mapped_channels": [
                {
                    "source": source,
                    "benchmark_channel": target,
                    "unit": unit,
                    "subsystem": "web_transport",
                }
                for source, target, unit in mapped
            ],
            "channel_coverage": channel_coverage,
            "source_field_coverage": source_field_coverage,
            "full_station_representation": False,
            "runs": len(sensor_items),
            "samples": None,
            "machines": None,
            "aggregate_fields": len(aggregate_header),
            "sensor_fields": len(sensor_header),
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C roll-to-roll mechanism analog; not semiconductor or OSAT validation.",
                "Four of 20 classified physical-valued source fields have exact Fleet Command mappings; selected-field coverage is not reported as 100% channel coverage.",
                "The four mapped fields have explicit physical semantics and units, but the dataset provides process-setting experiments rather than equipment-health labels.",
                "No confirmed-healthy exact-machine history or preregistered health split exists, so no Step 07/09/10 result is produced.",
                "The workbooks are schema-inspected only; controller settings, material geometry, and derived aggregate columns are not PHM channels.",
            ],
        }
    )
    return report
