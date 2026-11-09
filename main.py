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
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.classifier import classify
from src.mover import move_file


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


def organize(target_path: str, dry_run: bool = False) -> dict:
    """
    Run the organizer against a target directory.

    Args:
        target_path: Path to the directory to organize, as a string
            (e.g. from CLI args).
        dry_run: If True, prints/logs the plan without moving files.

    Returns:
        A summary dict with moved count, skipped count, and dry_run flag.

    Raises:
        NotADirectoryError: If target_path doesn't point to a real directory.
    """
    target_root = Path(target_path).expanduser().resolve()

    if not target_root.is_dir():
        raise NotADirectoryError(f"{target_root} is not a valid directory.")

    logger = setup_logging(target_root)
    mode_label = "DRY RUN" if dry_run else "LIVE"
    logger.info(f"Starting organizer on {target_root} [{mode_label}]")

    # Only scan files directly in target_root, not subfolders — otherwise
    # the script would recurse into the very category folders it just
    # created, which causes chaos on a second run.
    #
    # Hidden files (dotfiles) are never moved: sorting .env or .bashrc
    # into Other would be a nasty surprise. The .log files written by
    # earlier runs are skipped too.
    files = [
        f for f in target_root.iterdir()
        if f.is_file() and not f.name.startswith(".")
        and not f.name.endswith(".log")
    ]

    if not files:
        logger.info("No files found to organize.")
        return {"moved": 0, "skipped": 0, "dry_run": dry_run}

    moved_count = 0
    skipped_count = 0

    for file_path in files:
        category = classify(file_path)
        try:
            destination = move_file(file_path, category, target_root, dry_run)
            verb = "Would move" if dry_run else "Moved"
            logger.info(f"{verb}: {file_path.name} -> {category}/{destination.name}")
            moved_count += 1
        except PermissionError:
            logger.warning(f"Skipped (permission denied): {file_path.name}")
            skipped_count += 1
        except OSError as e:
            logger.warning(f"Skipped ({e}): {file_path.name}")
            skipped_count += 1

    logger.info(f"Done. {moved_count} file(s) organized, {skipped_count} skipped.")
    return {"moved": moved_count, "skipped": skipped_count, "dry_run": dry_run}


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
    args = parser.parse_args()

    try:
        organize(args.path, dry_run=args.dry_run)
    except NotADirectoryError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
