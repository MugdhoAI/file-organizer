"""
classifier.py

Decides which category a file belongs to, based on its extension.
No file-system operations happen here on purpose — this module only
answers questions, it never moves or touches files. Keeping "decide"
separate from "act" makes the code easier to test and easier to reason
about when something goes wrong.
"""

from pathlib import Path

# Extension -> category name.
# Add more mappings here as you need them; this dict is the single
# source of truth for classification rules.
CATEGORY_MAP: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".svg": "Images", ".webp": "Images",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".txt": "Documents", ".md": "Documents", ".xlsx": "Documents",
    ".csv": "Documents", ".pptx": "Documents",
    # Videos
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos", ".mkv": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code",
    ".json": "Code", ".java": "Code", ".cpp": "Code",
}

FALLBACK_CATEGORY = "Other"


def classify(file_path: Path) -> str:
    """
    Determine the category folder a file should be sorted into.

    Args:
        file_path: Path to the file being classified.

    Returns:
        The category name (e.g. "Images", "Documents"). Files whose
        extension isn't in CATEGORY_MAP fall back to "Other" rather
        than being skipped, so nothing is ever left unaccounted for.
    """
    extension = file_path.suffix.lower()
    return CATEGORY_MAP.get(extension, FALLBACK_CATEGORY)
