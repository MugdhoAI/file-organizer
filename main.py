#!/usr/bin/env python3
"""
File Organizer
---------------
Scans a target directory and sorts its files into category subfolders
(Images, Documents, Videos, Audio, Archives, Code, Other) based on
file extension.

Usage:
    python main.py --path ~/Downloads
    python main.py --path ~/Downloads --dry-run
    python main.py --path ~/Downloads --recursive
"""

import argparse
import fnmatch
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from src.classifier import CATEGORIES, classify, load_category_overrides
from src.mover import move_file, resolve_destination


def setup_logging(target_root: Path) -> logging.Logger:
    """
    Configure logging to write to both a .log file inside the target
    directory and to the console, so every run leaves an audit trail
    of what moved where.
    """
    log_file = target_root / f"organizer_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("file_organizer")
    logger.setLevel(logging.INFO)

    # Remove handlers left by any earlier organize() call in this
    # process, otherwise every line would be written once per call.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def is_organizer_log(name: str) -> bool:
    """
    True for log files written by earlier runs of this tool.

    Only the organizer's own timestamped logs are skipped. Other
    .log files, such as app.log from another program, are ordinary
    files and get organized like anything else.
    """
    return name.startswith("organizer_") and name.endswith(".log")


def collect_files(target_root: Path, recursive: bool) -> list[Path]:
    """
    Gather the files to organize, in sorted order so runs are
    deterministic: the log lines and the summary come out the same
    way every time for the same directory.

    Non-recursive mode only looks at files directly in target_root.
    Recursive mode walks subdirectories but never descends into
    category folders created by earlier runs, or into hidden folders.
    """
    if not recursive:
        return sorted(f for f in target_root.iterdir() if f.is_file())

    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(target_root):
        dirnames[:] = [
            d for d in dirnames if d not in CATEGORIES and not d.startswith(".")
        ]
        for name in sorted(filenames):
            files.append(Path(dirpath) / name)
    return sorted(files)


def organize(target_path: str, dry_run: bool = False, recursive: bool = False,
             exclude: list[str] | None = None,
             overrides: dict[str, str] | None = None) -> dict:
    """
    Run the organizer against a target directory.

    Args:
        target_path: Path to the directory to organize, as a string
            (e.g. from CLI args).
        dry_run: If True, prints/logs the plan without moving files.
        recursive: If True, also organize files in subdirectories.
        exclude: Optional list of glob patterns, matched against file
            names. Files matching any pattern are left exactly where
            they are, e.g. ["*.tmp", "draft*"].
        overrides: Optional user-defined category rules, as returned
            by load_category_overrides. They win over the built-in
            extension map.

    Returns:
        A summary dict with moved count, skipped count, dry_run flag,
        and per-category counts under "by_category".

    Raises:
        NotADirectoryError: If target_path doesn't point to a real directory.
    """
    target_root = Path(target_path).expanduser().resolve()

    if not target_root.is_dir():
        raise NotADirectoryError(f"{target_root} is not a valid directory.")

    logger = setup_logging(target_root)
    mode_label = "DRY RUN" if dry_run else "LIVE"
    logger.info(f"Starting organizer on {target_root} [{mode_label}]")

    # Hidden files (dotfiles) are never moved: sorting .env or .bashrc
    # into Other would be a nasty surprise. The organizer's own log
    # files from earlier runs are skipped too.
    candidates = collect_files(target_root, recursive)
    files = [
        f for f in candidates
        if not f.name.startswith(".") and not is_organizer_log(f.name)
    ]

    # Excluded files stay exactly where they are: a temp file or a
    # work-in-progress draft should never be swept into a folder.
    patterns = exclude or []
    files = [
        f for f in files
        if not any(fnmatch.fnmatch(f.name, pattern) for pattern in patterns)
    ]

    if not files:
        logger.info("No files found to organize.")
        return {"moved": 0, "skipped": 0, "dry_run": dry_run, "by_category": {}}

    moved_count = 0
    skipped_count = 0
    by_category: dict[str, int] = {}

    # Destinations claimed so far in this run. In a live run the disk
    # alone would reveal them, but a dry run moves nothing, so without
    # this set two same-named files would be planned onto one path.
    planned_destinations: set[Path] = set()

    for file_path in files:
        category = classify(file_path, overrides)
        try:
            destination = move_file(
                file_path, category, target_root, dry_run,
                taken=planned_destinations,
            )
            verb = "Would move" if dry_run else "Moved"
            logger.info(f"{verb}: {file_path.name} -> {category}/{destination.name}")
            moved_count += 1
            by_category[category] = by_category.get(category, 0) + 1
        except PermissionError:
            logger.warning(f"Skipped (permission denied): {file_path.name}")
            skipped_count += 1
        except OSError as e:
            logger.warning(f"Skipped ({e}): {file_path.name}")
            skipped_count += 1

    logger.info(f"Done. {moved_count} file(s) organized, {skipped_count} skipped.")
    if by_category:
        breakdown = ", ".join(
            f"{category} {count}"
            for category, count in sorted(by_category.items())
        )
        logger.info(f"By category: {breakdown}.")
    return {
        "moved": moved_count,
        "skipped": skipped_count,
        "dry_run": dry_run,
        "by_category": by_category,
    }


def parse_undo_moves(log_path: Path) -> list[tuple[str, str]]:
    """
    Read the moves recorded in one run log.

    Returns a list of (original name, destination relative to the
    target root) pairs, in the order they were logged. Only "Moved:"
    lines count: a dry run logs "Would move:" lines instead, and
    undoing a dry run correctly undoes nothing.
    """
    moves: list[tuple[str, str]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if " | Moved: " not in line:
            continue
        _, _, rest = line.partition(" | Moved: ")
        source, _, dest = rest.partition(" -> ")
        if source and dest:
            moves.append((source.strip(), dest.strip()))
    return moves


def undo_last_run(target_path: str) -> dict:
    """
    Reverse the most recent organize run in a directory, using its log file.

    Reads the newest organizer_*.log in the target directory and moves
    each file it recorded back to the target root, under its original
    name when that name is free. Files that are no longer where the
    log says they are count as missing. Empty category folders are
    left in place.

    Returns:
        A summary dict with undone count, missing count, and the name
        of the log file used.

    Raises:
        NotADirectoryError: If target_path doesn't point to a real directory.
        FileNotFoundError: If no organizer log exists in the directory.
    """
    target_root = Path(target_path).expanduser().resolve()

    if not target_root.is_dir():
        raise NotADirectoryError(f"{target_root} is not a valid directory.")

    logs = sorted(target_root.glob("organizer_*.log"))
    if not logs:
        raise FileNotFoundError(f"No organizer log found in {target_root}.")

    log_path = logs[-1]
    moves = parse_undo_moves(log_path)

    undone_count = 0
    missing_count = 0
    for source_name, dest_rel in moves:
        moved_path = target_root / dest_rel
        if not moved_path.exists():
            missing_count += 1
            continue
        destination = resolve_destination(target_root, Path(source_name))
        shutil.move(str(moved_path), str(destination))
        undone_count += 1

    return {
        "undone": undone_count,
        "missing": missing_count,
        "log": log_path.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Organize files in a directory into category subfolders."
    )
    parser.add_argument(
        "--path", required=True,
        help="Directory to organize, e.g. ~/Downloads"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would happen without moving any files."
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also organize files in subdirectories. Category folders "
        "and hidden folders are never descended into."
    )
    parser.add_argument(
        "--exclude", action="append", default=None, metavar="PATTERN",
        help="Leave files matching this glob pattern where they are, "
        "e.g. --exclude '*.tmp'. Repeatable."
    )
    parser.add_argument(
        "--config", default=None, metavar="FILE",
        help="JSON file mapping extensions to categories, e.g. "
        '\'{".nef": "Images"}\'. These rules win over the built-in map.'
    )
    parser.add_argument(
        "--undo", action="store_true",
        help="Reverse the most recent organize run in --path, using "
        "its log file. Moves files back to the target root."
    )
    args = parser.parse_args()

    if args.undo:
        try:
            summary = undo_last_run(args.path)
        except (NotADirectoryError, FileNotFoundError) as e:
            print(f"Error: {e}")
            sys.exit(1)
        print(
            f"Undone. {summary['undone']} file(s) restored, "
            f"{summary['missing']} missing."
        )
        return

    overrides = None
    if args.config:
        try:
            overrides = load_category_overrides(Path(args.config))
        except (OSError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    try:
        organize(args.path, dry_run=args.dry_run, recursive=args.recursive,
                 exclude=args.exclude, overrides=overrides)
    except NotADirectoryError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
