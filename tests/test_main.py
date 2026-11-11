"""
Unit tests for the file organizer: classification, collision handling,
file moves, and full organize() runs, including dry run, hidden files,
recursive mode, and repeated runs in one process.

Run from the repo root with:
    python -m unittest discover tests
"""

import io
import logging
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from main import collect_files, main, organize
from src.classifier import CATEGORIES, CATEGORY_MAP, classify
from src.mover import move_file, resolve_destination


def make_file(directory: Path, name: str, content: str = "x") -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


class TestClassify(unittest.TestCase):
    def test_known_extensions(self):
        cases = {
            "photo.jpg": "Images", "shot.PNG": "Images", "icon.svg": "Images",
            "report.pdf": "Documents", "notes.txt": "Documents",
            "sheet.xlsx": "Documents", "data.csv": "Documents",
            "clip.mp4": "Videos", "movie.mkv": "Videos",
            "song.mp3": "Audio", "track.flac": "Audio",
            "backup.zip": "Archives", "archive.tar.gz": "Archives",
            "script.py": "Code", "app.ts": "Code", "page.html": "Code",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(classify(Path(name)), expected)

    def test_new_extensions_added_to_map(self):
        cases = {
            "pic.bmp": "Images", "pic.tiff": "Images", "book.epub": "Documents",
            "clip.webm": "Videos", "podcast.ogg": "Audio",
            "bundle.tar.xz": "Archives", "app.go": "Code", "query.sql": "Code",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(classify(Path(name)), expected)

    def test_unknown_extension_falls_back_to_other(self):
        self.assertEqual(classify(Path("weird.xyz")), "Other")

    def test_no_extension_falls_back_to_other(self):
        self.assertEqual(classify(Path("Makefile")), "Other")

    def test_extension_match_is_case_insensitive(self):
        self.assertEqual(classify(Path("PHOTO.JPG")), "Images")

    def test_categories_cover_every_mapped_value(self):
        self.assertEqual(set(CATEGORIES), set(CATEGORY_MAP.values()) | {"Other"})


class TestResolveDestination(unittest.TestCase):
    def test_no_collision_returns_plain_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertEqual(
                resolve_destination(folder, Path("photo.jpg")),
                folder / "photo.jpg",
            )

    def test_collision_appends_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            make_file(folder, "photo.jpg")
            self.assertEqual(
                resolve_destination(folder, Path("photo.jpg")),
                folder / "photo_1.jpg",
            )

    def test_second_collision_increments_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            make_file(folder, "photo.jpg")
            make_file(folder, "photo_1.jpg")
            self.assertEqual(
                resolve_destination(folder, Path("photo.jpg")),
                folder / "photo_2.jpg",
            )

    def test_taken_paths_count_as_occupied(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            taken = {folder / "photo.jpg"}
            self.assertEqual(
                resolve_destination(folder, Path("photo.jpg"), taken=taken),
                folder / "photo_1.jpg",
            )


class TestMoveFile(unittest.TestCase):
    def test_live_move_creates_category_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = make_file(root, "photo.jpg")
            dest = move_file(source, "Images", root, dry_run=False)
            self.assertEqual(dest, root / "Images" / "photo.jpg")
            self.assertTrue(dest.exists())
            self.assertFalse(source.exists())

    def test_dry_run_moves_nothing_and_creates_no_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = make_file(root, "photo.jpg")
            dest = move_file(source, "Images", root, dry_run=True)
            self.assertEqual(dest, root / "Images" / "photo.jpg")
            self.assertTrue(source.exists())
            self.assertFalse((root / "Images").exists())

    def test_dry_run_with_shared_taken_set_plans_unique_destinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = make_file(root / "a", "report.pdf")
            second = make_file(root / "b", "report.pdf")
            taken = set()
            dest_a = move_file(first, "Documents", root, dry_run=True, taken=taken)
            dest_b = move_file(second, "Documents", root, dry_run=True, taken=taken)
            self.assertEqual(dest_a, root / "Documents" / "report.pdf")
            self.assertEqual(dest_b, root / "Documents" / "report_1.pdf")


class TestOrganize(unittest.TestCase):
    def test_live_run_sorts_files_and_returns_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, "photo.jpg")
            make_file(root, "report.pdf")
            make_file(root, "song.mp3")
            summary = organize(str(root))
            self.assertEqual(summary, {"moved": 3, "skipped": 0, "dry_run": False})
            self.assertTrue((root / "Images" / "photo.jpg").exists())
            self.assertTrue((root / "Documents" / "report.pdf").exists())
            self.assertTrue((root / "Audio" / "song.mp3").exists())

    def test_dry_run_moves_nothing_but_counts_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, "photo.jpg")
            summary = organize(str(root), dry_run=True)
            self.assertEqual(summary, {"moved": 1, "skipped": 0, "dry_run": True})
            self.assertTrue((root / "photo.jpg").exists())
            self.assertFalse((root / "Images").exists())

    def test_empty_directory_returns_zero_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                organize(tmp),
                {"moved": 0, "skipped": 0, "dry_run": False},
            )

    def test_invalid_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(NotADirectoryError):
                organize(str(Path(tmp) / "missing"))

    def test_collision_renames_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "Images", "photo.jpg", "original")
            make_file(root, "photo.jpg", "new")
            organize(str(root))
            self.assertEqual((root / "Images" / "photo.jpg").read_text(), "original")
            self.assertEqual((root / "Images" / "photo_1.jpg").read_text(), "new")

    def test_hidden_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, ".env")
            make_file(root, "photo.jpg")
            summary = organize(str(root))
            self.assertEqual(summary["moved"], 1)
            self.assertTrue((root / ".env").exists())

    def test_second_run_does_not_duplicate_log_handlers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, "photo.jpg")
            organize(str(root))
            organize(str(root))
            logger = logging.getLogger("file_organizer")
            self.assertEqual(len(logger.handlers), 2)

    def test_recursive_moves_nested_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "sub" / "deep", "song.mp3")
            make_file(root, "top.jpg")
            summary = organize(str(root), recursive=True)
            self.assertEqual(summary["moved"], 2)
            self.assertTrue((root / "Audio" / "song.mp3").exists())
            self.assertTrue((root / "Images" / "top.jpg").exists())

    def test_recursive_skips_files_already_in_category_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "Images", "old.jpg")
            summary = organize(str(root), recursive=True)
            self.assertEqual(summary["moved"], 0)
            self.assertTrue((root / "Images" / "old.jpg").exists())

    def test_non_recursive_leaves_nested_files_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = make_file(root / "sub", "song.mp3")
            summary = organize(str(root))
            self.assertEqual(summary["moved"], 0)
            self.assertTrue(nested.exists())

    def test_dry_run_recursive_plans_unique_destination_per_same_named_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "a", "report.pdf")
            make_file(root / "b", "report.pdf")
            out = io.StringIO()
            with redirect_stdout(out):
                summary = organize(str(root), dry_run=True, recursive=True)
            self.assertEqual(summary["moved"], 2)
            planned = [
                line.split("-> ")[-1].strip()
                for line in out.getvalue().splitlines()
                if "Would move" in line
            ]
            self.assertEqual(
                sorted(planned),
                ["Documents/report.pdf", "Documents/report_1.pdf"],
            )
            # A dry run still moves nothing.
            self.assertTrue((root / "a" / "report.pdf").exists())
            self.assertTrue((root / "b" / "report.pdf").exists())


class TestCollectFiles(unittest.TestCase):
    def test_non_recursive_only_sees_top_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, "top.jpg")
            make_file(root / "sub", "nested.jpg")
            names = {f.name for f in collect_files(root, recursive=False)}
            self.assertEqual(names, {"top.jpg"})

    def test_recursive_skips_hidden_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / ".hidden", "secret.jpg")
            make_file(root, "top.jpg")
            names = {f.name for f in collect_files(root, recursive=True)}
            self.assertEqual(names, {"top.jpg"})


class TestCli(unittest.TestCase):
    def test_main_dry_run_moves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root, "photo.jpg")
            with mock.patch("sys.argv", ["main.py", "--path", tmp, "--dry-run"]):
                main()
            self.assertTrue((root / "photo.jpg").exists())
            self.assertFalse((root / "Images").exists())

    def test_main_recursive_flag_reaches_organize(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "sub", "song.mp3")
            with mock.patch(
                "sys.argv", ["main.py", "--path", tmp, "--recursive"]
            ):
                main()
            self.assertTrue((root / "Audio" / "song.mp3").exists())

    def test_main_invalid_path_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = str(Path(tmp) / "missing")
            with mock.patch("sys.argv", ["main.py", "--path", bad]):
                with self.assertRaises(SystemExit) as ctx:
                    main()
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
