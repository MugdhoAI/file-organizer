"""
classifier.py

Decides which category a file belongs to, based on its extension.
No file-system operations happen here on purpose — this module only
answers questions, it never moves or touches files. Keeping "decide"
separate from "act" makes the code easier to test and easier to reason
about when something goes wrong.
"""

import json
from pathlib import Path

# Extension -> category name.
# Add more mappings here as you need them; this dict is the single
# source of truth for classification rules.
CATEGORY_MAP: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".svg": "Images", ".webp": "Images",
    ".bmp": "Images", ".tiff": "Images", ".tif": "Images",
    ".ico": "Images", ".heic": "Images", ".raw": "Images",
    ".psd": "Images",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".txt": "Documents", ".md": "Documents", ".xlsx": "Documents",
    ".csv": "Documents", ".pptx": "Documents",
    ".xls": "Documents", ".ppt": "Documents", ".odt": "Documents",
    ".ods": "Documents", ".odp": "Documents", ".epub": "Documents",
    ".mobi": "Documents", ".rtf": "Documents",
    # Videos
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos", ".mkv": "Videos",
    ".webm": "Videos", ".mpg": "Videos", ".mpeg": "Videos",
    ".wmv": "Videos", ".flv": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".ogg": "Audio", ".opus": "Audio", ".m4a": "Audio", ".aac": "Audio",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives",
    ".gz": "Archives", ".xz": "Archives", ".bz2": "Archives",
    ".dmg": "Archives", ".iso": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code",
    ".json": "Code", ".java": "Code", ".cpp": "Code",
    ".ts": "Code", ".tsx": "Code", ".jsx": "Code", ".c": "Code",
    ".h": "Code", ".hpp": "Code", ".go": "Code", ".rs": "Code",
    ".rb": "Code", ".php": "Code", ".sql": "Code", ".yaml": "Code",
    ".yml": "Code", ".toml": "Code", ".sh": "Code", ".xml": "Code",
}

FALLBACK_CATEGORY = "Other"

# Every category folder the organizer can create. Used to keep the
# recursive walk out of folders from earlier runs.
CATEGORIES: list[str] = sorted(set(CATEGORY_MAP.values()) | {FALLBACK_CATEGORY})


def load_category_overrides(config_path: Path) -> dict[str, str]:
    """
    Read user-defined category rules from a JSON file.

    The file maps extensions to category names, for example:
        {".nef": "Images", ".blend": "Code"}
    Keys must start with a dot and values must be non-empty strings.
    Extensions are lowercased on load, so ".NEF" and ".nef" mean the
    same thing.

    Raises:
        ValueError: If the file is not a JSON object, or a rule is
            malformed.
        OSError: If the file cannot be read.
    """
    with open(config_path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(
            f"{config_path} must contain a JSON object mapping "
            "extensions to categories."
        )
    overrides: dict[str, str] = {}
    for extension, category in data.items():
        if not isinstance(extension, str) or not extension.startswith("."):
            raise ValueError(
                f"Bad extension in {config_path}: {extension!r} "
                "(extensions must start with a dot)."
            )
        if not isinstance(category, str) or not category.strip():
            raise ValueError(
                f"Bad category in {config_path} for {extension!r}: "
                "categories must be non-empty strings."
            )
        overrides[extension.lower()] = category.strip()
    return overrides


def classify(file_path: Path, overrides: dict[str, str] | None = None) -> str:
    """
    Determine the category folder a file should be sorted into.

    Args:
        file_path: Path to the file being classified.
        overrides: Optional user-defined rules, as returned by
            load_category_overrides. They win over the built-in map,
            so a user can reassign an extension or add a new one.

    Returns:
        The category name (e.g. "Images", "Documents"). Files whose
        extension isn't in CATEGORY_MAP fall back to "Other" rather
        than being skipped, so nothing is ever left unaccounted for.
    """
    extension = file_path.suffix.lower()
    if overrides:
        category = overrides.get(extension)
        if category is not None:
            return category
    return CATEGORY_MAP.get(extension, FALLBACK_CATEGORY)
