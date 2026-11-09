"""Tests for backup manifest generation and verification."""

from pathlib import Path
import tempfile
import unittest

from backup_integrity.manifest import create_manifest, verify_manifest


class BackupManifestTests(unittest.TestCase):
    def test_created_manifest_verifies_unchanged_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data.txt").write_text("backup", encoding="utf-8")
            manifest = create_manifest(root)
            result = verify_manifest(root, manifest)
        self.assertTrue(result["verified"])
        self.assertEqual(result["checked"], 1)

    def test_detects_modified_missing_and_unexpected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "change.txt").write_text("before", encoding="utf-8")
            (root / "remove.txt").write_text("old", encoding="utf-8")
            manifest = create_manifest(root)
            (root / "change.txt").write_text("after", encoding="utf-8")
            (root / "remove.txt").unlink()
            (root / "extra.txt").write_text("extra", encoding="utf-8")
            result = verify_manifest(root, manifest)
        self.assertEqual(result["changed"], ["change.txt"])
        self.assertEqual(result["missing"], ["remove.txt"])
        self.assertEqual(result["unexpected"], ["extra.txt"])
        self.assertFalse(result["verified"])

    def test_rejects_path_traversal_in_manifest(self) -> None:
        manifest = {"format_version": 1, "algorithm": "sha256", "files": {
            "../outside.txt": {"sha256": "0" * 64, "size": 1}
        }}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                verify_manifest(directory, manifest)


if __name__ == "__main__":
    unittest.main()
