import json
import tempfile
import unittest
from pathlib import Path

from water_ai_research.audit import (
    build_manifest, cross_split_duplicates, text_fingerprint, verify_manifest, write_json,
)
from water_ai_research.splits import assert_disjoint_groups, connected_components, temporal_windows


class AuditSplitTests(unittest.TestCase):
    def test_text_identity_unicode_and_whitespace(self):
        self.assertEqual(text_fingerprint(" CAFÉ\n runoff "), text_fingerprint("cafe\u0301 runoff"))
        self.assertNotEqual(text_fingerprint("runoff!"), text_fingerprint("runoff"))

    def test_cross_split_duplicates_only(self):
        found = cross_split_duplicates({"train": ["Rain  fall", "rain fall"], "test": ["RAIN fall"]})
        self.assertEqual(list(found.values()), [["test", "train"]])
        self.assertEqual(cross_split_duplicates({"train": ["a", "a"]}), {})

    def test_manifest_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("rain", encoding="utf-8")
            manifest = build_manifest(root, ["a.txt"])
            verify_manifest(root, manifest)
            (root / "a.txt").write_text("flow", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_manifest(root, manifest)

    def test_manifest_path_escape_and_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("x")
            for names in [["../outside"], [str(root / "a.txt")], ["a.txt", "./a.txt"]]:
                with self.assertRaises(ValueError):
                    build_manifest(root, names)

    def test_manifest_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            (parent / "root").mkdir()
            (parent / "secret").write_text("not included")
            (parent / "root" / "link").symlink_to(parent / "secret")
            with self.assertRaises(ValueError):
                build_manifest(parent / "root", ["link"])

    def test_json_float_roundtrip(self):
        value = 0.10000000000000002
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "value.json"
            write_json(p, {"value": value})
            self.assertEqual(json.loads(p.read_text())["value"].hex(), value.hex())
            with self.assertRaises(ValueError):
                write_json(p, {"value": float("nan")})

    def test_components_transitive(self):
        # Rows 0 and 2 connect through row 1; empty rows stay distinct.
        self.assertEqual(connected_components([["a"], ["a", "b"], ["b"], [], []]), [0, 0, 0, 1, 2])

    def test_groups_reject_leak(self):
        assert_disjoint_groups({"train": ["basin1", "basin1"], "test": ["basin2"]})
        with self.assertRaises(ValueError):
            assert_disjoint_groups({"train": ["basin1"], "test": ["basin1"]})

    def test_window_support_is_disjoint(self):
        windows = temporal_windows(60, 4, 3, 25, 43, gap=2)
        used = {name: [i for w in items for i in range(w.input_start, w.target_stop)]
                for name, items in windows.items()}
        assert_disjoint_groups(used)
        self.assertEqual(max(used["train"]), 24)
        self.assertEqual(min(used["validation"]), 27)
        self.assertEqual(max(used["validation"]), 42)
        self.assertEqual(min(used["test"]), 45)
        for items in windows.values():
            for w in items:
                self.assertEqual(w.input_stop - w.input_start, 4)
                self.assertEqual(w.target_stop - w.target_start, 3)
                self.assertEqual(w.input_stop, w.target_start)

    def test_window_short_interval_and_invalid(self):
        windows = temporal_windows(12, 4, 3, 4, 8)
        self.assertTrue(all(not items for items in windows.values()))
        for arguments in [(10, 0, 1, 4, 8, 0), (10, 2, 1, 4, 8, 3), (10, 2, 1, 8, 4, 0)]:
            with self.assertRaises(ValueError):
                temporal_windows(*arguments)


if __name__ == "__main__":
    unittest.main()
