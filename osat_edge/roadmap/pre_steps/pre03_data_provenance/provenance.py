"""Small, fail-closed provenance boundary for external and REAL_OSAT bytes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Sequence
import unicodedata

from ..pre01_common.contracts import DataOrigin
from ..pre02_machine_registry.registry import STATIONS, StationDefinition


_VERIFICATION_TOKEN = object()
_CANONICAL_FILE_SET_V2_SCHEME = b"OSAT_FLEET_COMMAND:CANONICAL_FILE_SET_SHA256_V2"
_UINT64_BYTES = 8


class ProvenanceError(ValueError):
    """Raised when source identity or a provenance claim cannot be verified."""


class SourceIdentityKind(str, Enum):
    ARTIFACT_SHA256 = "ARTIFACT_SHA256"
    CANONICAL_FILE_SET_SHA256 = "CANONICAL_FILE_SET_SHA256"
    CANONICAL_FILE_SET_SHA256_V2 = "CANONICAL_FILE_SET_SHA256_V2"


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


def legacy_external_directory_hash(path: Path, files: Sequence[Path]) -> str:
    """LEGACY / EXTERNAL-BENCHMARK COMPATIBILITY ONLY.

    NOT VALID FOR REAL_OSAT PROVENANCE. This preserves already-committed
    external KUKA/NASA evidence identities that used ambiguous serialization.
    """

    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        name = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        with item.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def legacy_external_named_content_hash(items: Sequence[tuple[str, bytes]]) -> str:
    """LEGACY / EXTERNAL-BENCHMARK COMPATIBILITY ONLY.

    NOT VALID FOR REAL_OSAT PROVENANCE. File-content boundaries are not encoded.
    """

    digest = hashlib.sha256()
    for name, content in sorted(items):
        encoded = name.replace("\\", "/").encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(content)
    return digest.hexdigest()


def _uint64(value: int, field_name: str) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < 2**64:
        raise ProvenanceError(f"Canonical V2 {field_name} is outside uint64 range")
    return value.to_bytes(_UINT64_BYTES, "big")


def _normalize_relative_path(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ProvenanceError("Canonical V2 paths must be nonempty strings")
    if "\x00" in name:
        raise ProvenanceError("Canonical V2 paths may not contain NUL")
    portable = unicodedata.normalize("NFC", name.replace("\\", "/"))
    windows = PureWindowsPath(name)
    posix = PurePosixPath(portable)
    if windows.drive or windows.is_absolute() or posix.is_absolute():
        raise ProvenanceError("Canonical V2 paths must be relative")
    parts = portable.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ProvenanceError("Canonical V2 paths may not be empty or traverse directories")
    return "/".join(parts)


def _canonical_file_set_preimage_from_records(
    records: Sequence[tuple[str, int, bytes]],
) -> bytes:
    if not records:
        raise ProvenanceError("REAL_OSAT canonical file set is empty")
    normalized: list[tuple[str, int, bytes]] = []
    seen: set[str] = set()
    for name, content_length, content_digest in records:
        path = _normalize_relative_path(name)
        if path in seen:
            raise ProvenanceError(f"Duplicate normalized canonical V2 path {path!r}")
        seen.add(path)
        if not isinstance(content_digest, bytes) or len(content_digest) != hashlib.sha256().digest_size:
            raise ProvenanceError("Canonical V2 content digests must be raw SHA-256 values")
        normalized.append((path, content_length, content_digest))

    representation = bytearray()
    representation.extend(_uint64(len(_CANONICAL_FILE_SET_V2_SCHEME), "scheme length"))
    representation.extend(_CANONICAL_FILE_SET_V2_SCHEME)
    representation.extend(_uint64(len(normalized), "file count"))
    for path, content_length, content_digest in sorted(normalized, key=lambda item: item[0]):
        path_bytes = path.encode("utf-8")
        representation.extend(_uint64(len(path_bytes), "path byte length"))
        representation.extend(path_bytes)
        representation.extend(_uint64(content_length, "content byte length"))
        representation.extend(content_digest)
    return bytes(representation)


def canonical_file_set_preimage_v2(items: Sequence[tuple[str, bytes]]) -> bytes:
    """Return the unambiguous V2 representation for named in-memory bytes."""

    records: list[tuple[str, int, bytes]] = []
    for name, content in items:
        if not isinstance(content, bytes):
            raise ProvenanceError("Canonical V2 file content must be bytes")
        records.append((name, len(content), hashlib.sha256(content).digest()))
    return _canonical_file_set_preimage_from_records(records)


def canonical_file_set_sha256_v2(items: Sequence[tuple[str, bytes]]) -> str:
    """Hash an unambiguous, versioned canonical representation of named bytes."""

    return hashlib.sha256(canonical_file_set_preimage_v2(items)).hexdigest()


def _file_sha256_and_length(path: Path) -> tuple[bytes, int]:
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            length += len(block)
            digest.update(block)
    return digest.digest(), length


def canonical_directory_preimage_v2(path: Path, files: Sequence[Path]) -> bytes:
    """Return the V2 representation for files contained by one directory."""

    root = path.resolve()
    if not root.is_dir():
        raise ProvenanceError("Canonical file-set source must be a directory")
    records: list[tuple[str, int, bytes]] = []
    for item in files:
        candidate = Path(item)
        if candidate.is_symlink():
            raise ProvenanceError("REAL_OSAT source file sets may not contain symlinks")
        if not candidate.is_file():
            raise ProvenanceError("Canonical V2 entries must be existing files")
        try:
            name = candidate.resolve().relative_to(root).as_posix()
        except ValueError as error:
            raise ProvenanceError("Canonical V2 files must remain inside the source directory") from error
        content_digest, content_length = _file_sha256_and_length(candidate)
        records.append((name, content_length, content_digest))
    return _canonical_file_set_preimage_from_records(records)


def canonical_directory_sha256_v2(path: Path, files: Sequence[Path]) -> str:
    """Hash the V2 canonical representation of one directory file set."""

    return hashlib.sha256(canonical_directory_preimage_v2(path, files)).hexdigest()


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
    elif contract.source_identity_kind is SourceIdentityKind.CANONICAL_FILE_SET_SHA256_V2:
        files = _canonical_files(selected)
        computed = canonical_directory_sha256_v2(selected, files)
        names = tuple(
            _normalize_relative_path(item.relative_to(selected).as_posix())
            for item in files
        )
    else:
        raise ProvenanceError(
            "Legacy canonical file-set hashing cannot establish REAL_OSAT provenance; "
            "use CANONICAL_FILE_SET_SHA256_V2"
        )

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
    "canonical_directory_preimage_v2",
    "canonical_directory_sha256_v2",
    "canonical_file_set_preimage_v2",
    "canonical_file_set_sha256_v2",
    "declare_real_osat_origin",
    "legacy_external_directory_hash",
    "legacy_external_named_content_hash",
    "md5_file",
    "sha256_file",
    "verify_real_osat_source",
]
