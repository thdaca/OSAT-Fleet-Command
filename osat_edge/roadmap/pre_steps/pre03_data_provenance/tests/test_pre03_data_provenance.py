from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from osat_edge.roadmap.pre_steps.pre01_common.contracts import DataOrigin
from osat_edge.roadmap.pre_steps.pre03_data_provenance.provenance import (
    OsatProvenanceBasis,
    ProvenanceError,
    RealOsatChannelMapping,
    RealOsatLabelType,
    RealOsatProvenance,
    SourceIdentityKind,
    VerifiedRealOsatSource,
    canonical_directory_preimage_v2,
    canonical_directory_sha256_v2,
    canonical_file_set_preimage_v2,
    canonical_file_set_sha256_v2,
    declare_real_osat_origin,
    legacy_external_directory_hash,
    legacy_external_named_content_hash,
    verify_real_osat_source,
)


class DataProvenanceTests(unittest.TestCase):
    @staticmethod
    def _osat_contract(
        *label_types: RealOsatLabelType,
        evidence_class: str = "A",
        source_sha256: str = "0" * 64,
        canonical_station_id: str | None = "WB-04",
        channel_mappings: tuple[RealOsatChannelMapping, ...] | None = None,
        equipment: str = "production wire bonder",
        source_identity_kind: SourceIdentityKind = SourceIdentityKind.ARTIFACT_SHA256,
    ) -> RealOsatProvenance:
        if channel_mappings is None:
            channel_mappings = (
                RealOsatChannelMapping(
                    "Bond Force", "bond_force", "gf", "per-bond head-force feedback"
                ),
            ) if canonical_station_id is not None else ()
        return RealOsatProvenance(
            dataset_citation="De-identified OSAT partner export under reviewed agreement",
            source_sha256=source_sha256,
            source_identity_kind=source_identity_kind,
            osat_provenance_basis=OsatProvenanceBasis.OPERATOR_ATTESTATION,
            osat_provenance="Partner attests that the source facility performs outsourced assembly/test",
            machine_pseudonym="WB-PSEUDO-01",
            equipment=equipment,
            canonical_station_id=canonical_station_id,
            channel_mappings=channel_mappings,
            boundary_semantics="timestamped bond cycles grouped by pseudonymous machine and run",
            provenance_statement="De-identified export; customer and recipe names removed",
            label_types=label_types or (RealOsatLabelType.UNLABELED,),
            evidence_class=evidence_class,
        )

    def test_real_osat_origin_requires_complete_provenance_contract(self) -> None:
        with self.assertRaisesRegex(ProvenanceError, "byte-verified"):
            declare_real_osat_origin(None)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "partner-export.bin"
            source.write_bytes(b"authorized de-identified OSAT export")
            contract = self._osat_contract(
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()
            )
            verified = verify_real_osat_source(contract, source)
        self.assertIs(DataOrigin.REAL_OSAT, declare_real_osat_origin(verified))
        self.assertTrue(verified.canonically_executable)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            RealOsatProvenance(**{**contract.__dict__, "source_sha256": "not-a-hash"})

    def test_fabricated_hash_and_random_compatible_file_cannot_establish_real_osat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "compatible.csv"
            source.write_text("Bond Force\n40\n", encoding="utf-8")
            contract = self._osat_contract(source_sha256="a" * 64)
            with self.assertRaisesRegex(ProvenanceError, "do not match"):
                verify_real_osat_source(contract, source)
            with self.assertRaisesRegex(ProvenanceError, "byte-verified"):
                declare_real_osat_origin(contract)  # type: ignore[arg-type]

    def test_unverified_osat_paper_and_synthetic_origin_are_not_executable_sources(self) -> None:
        paper_only = self._osat_contract(source_sha256="b" * 64)
        with tempfile.TemporaryDirectory() as directory:
            missing_attachment = Path(directory) / "unpublished-supplement.csv"
            with self.assertRaisesRegex(ProvenanceError, "existing file"):
                verify_real_osat_source(paper_only, missing_attachment)
        for unverified in (paper_only, DataOrigin.SYNTHETIC):
            with self.subTest(unverified=unverified), self.assertRaisesRegex(
                ProvenanceError, "byte-verified"
            ):
                declare_real_osat_origin(unverified)  # type: ignore[arg-type]

    def test_verified_source_result_cannot_be_constructed_without_byte_verification(self) -> None:
        contract = self._osat_contract(source_sha256="c" * 64)
        with self.assertRaisesRegex(ProvenanceError, "only be created"):
            VerifiedRealOsatSource(contract, "c" * 64, ("claimed.csv",), object())

    def test_canonical_station_channel_and_unit_claims_fail_closed(self) -> None:
        with self.assertRaisesRegex(ProvenanceError, "Unknown canonical station"):
            self._osat_contract(canonical_station_id="NOT-A-STATION")
        with self.assertRaisesRegex(ProvenanceError, "not a channel"):
            self._osat_contract(
                channel_mappings=(
                    RealOsatChannelMapping("Mystery", "not_a_real_channel", "bananas", "unknown proxy"),
                )
            )
        with self.assertRaisesRegex(ProvenanceError, "exact unit"):
            self._osat_contract(
                channel_mappings=(
                    RealOsatChannelMapping("Bond Force", "bond_force", "bananas", "per-bond force"),
                )
            )

    def test_verified_real_osat_origin_may_be_noncanonical_auxiliary_equipment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pump-export.bin"
            source.write_bytes(b"authorized auxiliary pump export")
            auxiliary = self._osat_contract(
                RealOsatLabelType.MAINTENANCE_EVENT,
                evidence_class="C",
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                canonical_station_id=None,
                equipment="auxiliary liquid-ring vacuum pump",
            )
            verified = verify_real_osat_source(auxiliary, source)
        self.assertIs(DataOrigin.REAL_OSAT, declare_real_osat_origin(verified))
        self.assertFalse(verified.canonically_executable)
        self.assertIsNone(auxiliary.canonical_station_id)
        self.assertEqual((), auxiliary.channel_mappings)

    def test_real_osat_canonical_file_set_identity_is_computed_from_supplied_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "first.csv").write_text("x\n1\n", encoding="utf-8")
            (source / "second.csv").write_text("y\n2\n", encoding="utf-8")
            files = tuple(sorted(source.iterdir()))
            contract = self._osat_contract(
                source_sha256=canonical_directory_sha256_v2(source, files),
                source_identity_kind=SourceIdentityKind.CANONICAL_FILE_SET_SHA256_V2,
            )
            verified = verify_real_osat_source(contract, source)
        self.assertEqual(("first.csv", "second.csv"), verified.verified_files)

    def test_exact_legacy_collision_is_distinct_in_v2_and_legacy_is_rejected(self) -> None:
        set_a = (("a", b"\x00\x00\x00\x01bX"),)
        set_b = (("a", b""), ("b", b"X"))
        self.assertEqual(
            legacy_external_named_content_hash(set_a),
            legacy_external_named_content_hash(set_b),
        )
        self.assertNotEqual(
            canonical_file_set_preimage_v2(set_a),
            canonical_file_set_preimage_v2(set_b),
        )
        self.assertNotEqual(
            canonical_file_set_sha256_v2(set_a),
            canonical_file_set_sha256_v2(set_b),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_a = root / "set-a"
            source_b = root / "set-b"
            source_a.mkdir()
            source_b.mkdir()
            (source_a / "a").write_bytes(set_a[0][1])
            (source_b / "a").write_bytes(b"")
            (source_b / "b").write_bytes(b"X")
            files_a = tuple(source_a.iterdir())
            files_b = tuple(source_b.iterdir())
            legacy_a = legacy_external_directory_hash(source_a, files_a)
            legacy_b = legacy_external_directory_hash(source_b, files_b)
            self.assertEqual(legacy_a, legacy_b)
            with self.assertRaisesRegex(ProvenanceError, "Legacy canonical"):
                verify_real_osat_source(
                    self._osat_contract(
                        source_sha256=legacy_a,
                        source_identity_kind=SourceIdentityKind.CANONICAL_FILE_SET_SHA256,
                    ),
                    source_a,
                )
            verified = verify_real_osat_source(
                self._osat_contract(
                    source_sha256=canonical_directory_sha256_v2(source_a, files_a),
                    source_identity_kind=SourceIdentityKind.CANONICAL_FILE_SET_SHA256_V2,
                ),
                source_a,
            )
        self.assertEqual(("a",), verified.verified_files)

    def test_v2_is_order_independent_and_supports_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "z-empty").write_bytes(b"")
            (source / "a-empty").write_bytes(b"")
            (source / "middle").write_bytes(b"payload")
            files = tuple(source.iterdir())
            forward = canonical_directory_preimage_v2(source, files)
            reverse = canonical_directory_preimage_v2(source, tuple(reversed(files)))
        self.assertEqual(forward, reverse)
        self.assertEqual(
            canonical_file_set_sha256_v2((("empty", b""),)),
            canonical_file_set_sha256_v2((("empty", b""),)),
        )
        self.assertNotEqual(
            canonical_file_set_preimage_v2((("empty", b""),)),
            canonical_file_set_preimage_v2((("empty-a", b""), ("empty-b", b""))),
        )
        with self.assertRaisesRegex(ProvenanceError, "empty"):
            canonical_file_set_preimage_v2(())

    def test_v2_normalizes_portable_paths_and_rejects_unsafe_names(self) -> None:
        slash = canonical_file_set_preimage_v2((("folder/file.csv", b"x"),))
        backslash = canonical_file_set_preimage_v2((("folder\\file.csv", b"x"),))
        self.assertEqual(slash, backslash)
        composed = canonical_file_set_preimage_v2((("caf\u00e9/data.csv", b"x"),))
        decomposed = canonical_file_set_preimage_v2((("cafe\u0301/data.csv", b"x"),))
        self.assertEqual(composed, decomposed)
        with self.assertRaisesRegex(ProvenanceError, "Duplicate normalized"):
            canonical_file_set_preimage_v2(
                (("folder/file.csv", b"a"), ("folder\\file.csv", b"b"))
            )
        with self.assertRaisesRegex(ProvenanceError, "Duplicate normalized"):
            canonical_file_set_preimage_v2(
                (("caf\u00e9.csv", b"a"), ("cafe\u0301.csv", b"b"))
            )
        for unsafe in ("../secret.csv", "safe/../secret.csv", "/absolute.csv", "C:\\absolute.csv"):
            with self.subTest(path=unsafe), self.assertRaisesRegex(
                ProvenanceError, "relative|traverse"
            ):
                canonical_file_set_preimage_v2(((unsafe, b"x"),))

    def test_v2_representation_distinguishes_all_structural_changes(self) -> None:
        variants = (
            (("a", b"AB"),),
            (("a", b"AC"),),
            (("b", b"AB"),),
            (("same-a", b"AB"),),
            (("same-b", b"AB"),),
            (("part-a", b"A"), ("part-b", b"B")),
            (("part-a", b"AB"),),
            (("left", b"A"), ("right", b"B")),
            (("left", b"AB"),),
        )
        representations = tuple(canonical_file_set_preimage_v2(items) for items in variants)
        self.assertEqual(len(variants), len(set(representations)))

    def test_osat_origin_evidence_class_and_label_semantics_remain_separate(self) -> None:
        process_record = self._osat_contract(
            RealOsatLabelType.MACHINE_ALARM,
            RealOsatLabelType.MES_SCRAP,
            RealOsatLabelType.PROCESS_QUALITY,
            evidence_class="C",
        )
        self.assertEqual("C", process_record.evidence_class)
        self.assertFalse(process_record.supports_confirmed_fault)
        self.assertFalse(process_record.supports_confirmed_healthy)
        maintenance_only = self._osat_contract(RealOsatLabelType.MAINTENANCE_EVENT)
        self.assertFalse(maintenance_only.supports_confirmed_fault)
        self.assertFalse(maintenance_only.supports_confirmed_healthy)
        adjudicated = self._osat_contract(
            RealOsatLabelType.ADJUDICATED_HEALTHY_INTERVAL,
            RealOsatLabelType.ADJUDICATED_FAULT,
        )
        self.assertTrue(adjudicated.supports_confirmed_fault)
        self.assertTrue(adjudicated.supports_confirmed_healthy)


if __name__ == "__main__":
    unittest.main()
