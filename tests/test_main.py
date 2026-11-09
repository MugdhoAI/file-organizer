"""
Unit tests for the file organizer: classification, collision handling,
file moves, and full organize() runs, including dry run.

Run from the repo root with:
    python -m unittest discover tests
"""

import logging
import tempfile
import unittest
from pathlib import Path

from main import organize
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
            "backup.zip": "Archives", "archive.tar": "Archives",
            "script.py": "Code", "app.js": "Code", "page.html": "Code",
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

    def test_categories_cover_every_mapped_value(self):
        self.assertEqual(set(CATEGORIES), set(CATEGORY_MAP.values()) | {"Other"})

    def test_unknown_extension_falls_back_to_other(self):
        self.assertEqual(classify(Path("weird.xyz")), "Other")

    def test_no_extension_falls_back_to_other(self):
        self.assertEqual(classify(Path("Makefile")), "Other")

    def test_extension_match_is_case_insensitive(self):
        self.assertEqual(classify(Path("PHOTO.JPG")), "Images")


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


class TestOrganize(unittest.TestCase):
    def test_live_run_sorts_files(self):
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

    def test_dry_run_moves_nothing(self):
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

    def test_collision_renames_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_file(root / "Images", "photo.jpg", "original")
            make_file(root, "photo.jpg", "new")
            organize(str(root))
            self.assertEqual((root / "Images" / "photo.jpg").read_text(), "original")
            self.assertEqual((root / "Images" / "photo_1.jpg").read_text(), "new")


if __name__ == "__main__":
    unittest.main()
