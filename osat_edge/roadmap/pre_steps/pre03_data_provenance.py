"""Small, fail-closed provenance boundary for external and REAL_OSAT bytes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
from pathlib import Path
import re
from typing import Sequence

from .pre01_common import DataOrigin
from .pre02_machine_registry import STATIONS, StationDefinition


_VERIFICATION_TOKEN = object()


class ProvenanceError(ValueError):
    """Raised when source identity or a provenance claim cannot be verified."""


class SourceIdentityKind(str, Enum):
    ARTIFACT_SHA256 = "ARTIFACT_SHA256"
    CANONICAL_FILE_SET_SHA256 = "CANONICAL_FILE_SET_SHA256"


class OsatProvenanceBasis(str, Enum):
    FACILITY_OPERATOR_PUBLICATION = "FACILITY_OPERATOR_PUBLICATION"
    OPERATOR_ATTESTATION = "OPERATOR_ATTESTATION"
    AUTHORIZED_DATA_AGREEMENT = "AUTHORIZED_DATA_AGREEMENT"


class RealOsatLabelType(str, Enum):
    """Label semantics that a future de-identified OSAT replay may declare."""

    UNLABELED = "UNLABELED"
    MACHINE_ALARM = "MACHINE_ALARM"
    PROCESS_QUALITY = "PROCESS_QUALITY"
    MES_SCRAP = "MES_SCRAP"
    MAINTENANCE_EVENT = "MAINTENANCE_EVENT"
    ADJUDICATED_HEALTHY_INTERVAL = "ADJUDICATED_HEALTHY_INTERVAL"
    ADJUDICATED_FAULT = "ADJUDICATED_FAULT"


@dataclass(frozen=True)
class RealOsatChannelMapping:
    source_name: str
    canonical_channel: str
    unit: str
    acquisition_semantics: str

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                self.source_name,
                self.canonical_channel,
                self.unit,
                self.acquisition_semantics,
            )
        ):
            raise ProvenanceError(
                "REAL_OSAT channel mappings require exact names, units, and semantics"
            )


def _station_by_id(station_id: str) -> StationDefinition:
    matches = [station for station in STATIONS.values() if station.station_id == station_id]
    if len(matches) != 1:
        raise ProvenanceError(f"Unknown canonical station ID {station_id!r}")
    return matches[0]


@dataclass(frozen=True)
class RealOsatProvenance:
    """Declaration to verify against bytes before REAL_OSAT is exposed."""

    dataset_citation: str
    source_sha256: str
    source_identity_kind: SourceIdentityKind
    osat_provenance_basis: OsatProvenanceBasis
    osat_provenance: str
    machine_pseudonym: str
    equipment: str
    canonical_station_id: str | None
    channel_mappings: tuple[RealOsatChannelMapping, ...]
    boundary_semantics: str
    provenance_statement: str
    label_types: tuple[RealOsatLabelType, ...]
    evidence_class: str

    def __post_init__(self) -> None:
        required = (
            self.dataset_citation,
            self.osat_provenance,
            self.machine_pseudonym,
            self.equipment,
            self.boundary_semantics,
            self.provenance_statement,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ProvenanceError("REAL_OSAT provenance fields must be explicit and nonempty")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ProvenanceError(
                "REAL_OSAT source SHA-256 must be 64 lowercase hexadecimal characters"
            )
        if not isinstance(self.source_identity_kind, SourceIdentityKind):
            raise ProvenanceError("REAL_OSAT source identity kind must be explicit")
        if not isinstance(self.osat_provenance_basis, OsatProvenanceBasis):
            raise ProvenanceError("REAL_OSAT origin requires a reviewed provenance basis")
        if any(
            not isinstance(item, RealOsatChannelMapping) for item in self.channel_mappings
        ):
            raise ProvenanceError("REAL_OSAT channel mappings must use the exact mapping contract")
        if len({item.source_name for item in self.channel_mappings}) != len(
            self.channel_mappings
        ):
            raise ProvenanceError("REAL_OSAT source channel names must be unique")
        if len({item.canonical_channel for item in self.channel_mappings}) != len(
            self.channel_mappings
        ):
            raise ProvenanceError("REAL_OSAT canonical channel mappings must be one-to-one")
        if not self.label_types or any(
            not isinstance(item, RealOsatLabelType) for item in self.label_types
        ):
            raise ProvenanceError(
                "REAL_OSAT label semantics must be declared, including UNLABELED"
            )
        if len(set(self.label_types)) != len(self.label_types):
            raise ProvenanceError("REAL_OSAT label semantics must be unique")
        if self.evidence_class not in {"A", "B", "C", "D"}:
            raise ProvenanceError("REAL_OSAT evidence class must be A, B, C, or D")

        if self.canonical_station_id is None:
            if self.channel_mappings:
                raise ProvenanceError(
                    "Canonical channel mappings require an explicit canonical station"
                )
            return
        if not self.canonical_station_id.strip():
            raise ProvenanceError(
                "REAL_OSAT canonical station ID must be nonempty when supplied"
            )
        station = _station_by_id(self.canonical_station_id)
        channels = {channel.name: channel for channel in station.channels}
        for mapping in self.channel_mappings:
            channel = channels.get(mapping.canonical_channel)
            if channel is None:
                raise ProvenanceError(
                    f"{mapping.canonical_channel!r} is not a channel on "
                    f"{station.station_id}"
                )
            if mapping.unit != channel.unit:
                raise ProvenanceError(
                    f"{mapping.canonical_channel!r} requires exact unit {channel.unit!r}"
                )

    @property
    def supports_confirmed_fault(self) -> bool:
        return RealOsatLabelType.ADJUDICATED_FAULT in self.label_types

    @property
    def supports_confirmed_healthy(self) -> bool:
        return RealOsatLabelType.ADJUDICATED_HEALTHY_INTERVAL in self.label_types

    @property
    def canonically_executable(self) -> bool:
        return self.canonical_station_id is not None and bool(self.channel_mappings)


@dataclass(frozen=True)
class VerifiedRealOsatSource:
    """A REAL_OSAT declaration whose pinned identity matches supplied bytes."""

    provenance: RealOsatProvenance
    computed_sha256: str
    verified_files: tuple[str, ...]
    _verification_token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._verification_token is not _VERIFICATION_TOKEN:
            raise ProvenanceError(
                "Verified REAL_OSAT sources can only be created by byte verification"
            )

    @property
    def origin(self) -> DataOrigin:
        return DataOrigin.REAL_OSAT

    @property
    def canonically_executable(self) -> bool:
        return self.provenance.canonically_executable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def directory_hash(path: Path, files: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        name = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        with item.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def named_content_hash(items: Sequence[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, content in sorted(items):
        encoded = name.replace("\\", "/").encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(content)
    return digest.hexdigest()


def _canonical_files(source: Path) -> tuple[Path, ...]:
    if not source.is_dir():
        raise ProvenanceError("Canonical file-set source must be a directory")
    files: list[Path] = []
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ProvenanceError("REAL_OSAT source file sets may not contain symlinks")
        if item.is_file():
            files.append(item)
    if not files:
        raise ProvenanceError("REAL_OSAT canonical file set is empty")
    return tuple(files)


def verify_real_osat_source(
    contract: RealOsatProvenance | None,
    source: str | Path,
) -> VerifiedRealOsatSource:
    """Compute source identity and expose REAL_OSAT only after an exact match."""

    if contract is None:
        raise ProvenanceError("REAL_OSAT cannot be asserted without a provenance contract")
    if not isinstance(contract, RealOsatProvenance):
        raise ProvenanceError("REAL_OSAT requires the typed provenance contract")
    selected = Path(source).resolve()
    if selected.is_symlink():
        raise ProvenanceError("REAL_OSAT source may not be a symbolic link")

    if contract.source_identity_kind is SourceIdentityKind.ARTIFACT_SHA256:
        if not selected.is_file():
            raise ProvenanceError("REAL_OSAT artifact source must be an existing file")
        computed = sha256_file(selected)
        names = (selected.name,)
    else:
        files = _canonical_files(selected)
        computed = directory_hash(selected, files)
        names = tuple(item.relative_to(selected).as_posix() for item in files)

    if not hmac.compare_digest(computed, contract.source_sha256):
        raise ProvenanceError("Supplied REAL_OSAT bytes do not match the declared source hash")
    return VerifiedRealOsatSource(contract, computed, names, _VERIFICATION_TOKEN)


def declare_real_osat_origin(verified: VerifiedRealOsatSource | None) -> DataOrigin:
    """Return REAL_OSAT only for a source produced by byte-level verification."""

    if (
        not isinstance(verified, VerifiedRealOsatSource)
        or verified._verification_token is not _VERIFICATION_TOKEN
    ):
        raise ProvenanceError("REAL_OSAT requires a byte-verified source identity")
    return verified.origin


__all__ = [
    "OsatProvenanceBasis",
    "ProvenanceError",
    "RealOsatChannelMapping",
    "RealOsatLabelType",
    "RealOsatProvenance",
    "SourceIdentityKind",
    "VerifiedRealOsatSource",
    "declare_real_osat_origin",
    "directory_hash",
    "md5_file",
    "named_content_hash",
    "sha256_file",
    "verify_real_osat_source",
]
