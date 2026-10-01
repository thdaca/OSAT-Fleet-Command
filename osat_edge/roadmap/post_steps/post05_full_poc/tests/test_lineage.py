"""Historical preservation and current-source drift are independent checks."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from .. import lineage


class LineageTests(unittest.TestCase):
    def test_current_source_drift_is_rejected(self):
        changed = {**lineage.implementation_identity(), "sha256": "0" * 64}
        with patch.object(lineage, "implementation_identity", return_value=changed):
            with self.assertRaisesRegex(ValueError, "snapshot 2 pin"):
                lineage.frozen_lineage()

    def test_preserved_source_content_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            corrupted = Path(directory) / "sources.zip"
            with zipfile.ZipFile(lineage.FROZEN_SOURCE_ARCHIVE) as original:
                with zipfile.ZipFile(corrupted, "w") as output:
                    for index, name in enumerate(original.namelist()):
                        value = original.read(name)
                        output.writestr(name, value + b"changed" if index == 0 else value)
            with patch.object(lineage, "FROZEN_SOURCE_ARCHIVE", corrupted):
                with self.assertRaisesRegex(ValueError, "Preserved frozen scientific/source bytes"):
                    lineage.frozen_lineage()
