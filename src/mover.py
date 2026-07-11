"""
mover.py

Handles the actual filesystem operations: creating category folders
and moving files into them. This is the only module that touches disk,
which keeps the "risky" code isolated and easy to audit.
"""

import shutil
from pathlib import Path


def resolve_destination(dest_folder: Path, file_path: Path) -> Path:
    """
    Work out the final destination path for a file, avoiding overwrites.

    If "Images/photo.jpg" already exists, this returns "Images/photo_1.jpg",
    then "photo_2.jpg", and so on, instead of silently overwriting an
    existing file with the same name.

    Args:
        dest_folder: The category folder the file is being moved into.
        file_path: The original file being moved.

    Returns:
        A Path that is guaranteed not to already exist.
    """
    candidate = dest_folder / file_path.name
    if not candidate.exists():
        return candidate

    stem = file_path.stem       # filename without extension
    extension = file_path.suffix
    counter = 1
    while True:
        candidate = dest_folder / f"{stem}_{counter}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_file(file_path: Path, category: str, target_root: Path, dry_run: bool) -> Path:
    """
    Move a single file into its category folder.

    Args:
        file_path: The file to move.
        category: The category name, e.g. "Images".
        target_root: The root directory being organized.
        dry_run: If True, no actual move happens — the planned
            destination is still calculated and returned so it can
            be logged/printed for preview.

    Returns:
        The destination path the file was (or would be) moved to.

    Raises:
        PermissionError: If the file can't be moved due to OS permissions.
            Caller is expected to catch this and continue with other files
            rather than let one bad file crash the whole run.
    """
    dest_folder = target_root / category
    if not dry_run:
        dest_folder.mkdir(exist_ok=True)

    destination = resolve_destination(dest_folder, file_path)

    if not dry_run:
        shutil.move(str(file_path), str(destination))

    return destination
