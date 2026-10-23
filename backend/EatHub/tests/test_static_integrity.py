import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from EatHub.static_integrity import ALGORITHM, StaticIntegrityError, build_manifest


class StaticIntegrityTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_covers_paths_and_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "z.txt").write_bytes(b"last")
            (root / "nested").mkdir()
            (root / "nested" / "a.txt").write_bytes(b"first")

            actual = build_manifest(root)
            expected_files = [
                {
                    "path": "nested/a.txt",
                    "size": 5,
                    "sha256": hashlib.sha256(b"first").hexdigest(),
                },
                {
                    "path": "z.txt",
                    "size": 4,
                    "sha256": hashlib.sha256(b"last").hexdigest(),
                },
            ]
            canonical = json.dumps(
                {"algorithm": ALGORITHM, "files": expected_files},
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
            self.assertEqual(
                actual,
                {
                    "algorithm": ALGORITHM,
                    "files": 2,
                    "bytes": 9,
                    "sha256": hashlib.sha256(canonical).hexdigest(),
                },
            )

    def test_empty_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(StaticIntegrityError):
                build_manifest(temporary)

    def test_symbolic_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.txt"
            target.write_text("content", encoding="utf-8")
            link = root / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available in this test environment")
            with self.assertRaises(StaticIntegrityError):
                build_manifest(root)


if __name__ == "__main__":
    unittest.main()
