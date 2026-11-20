# File Organizer

A command line tool that automatically sorts files in a directory into category subfolders such as Images, Documents, Videos, Audio, Archives, and Code based on file extension. It is designed for cleaning up folders such as Downloads without manual sorting.

## Demo

```
$ python main.py --path ~/Downloads --dry-run
08:19:04 | Starting organizer on /home/user/Downloads [DRY RUN]
08:19:04 | Would move: report.pdf -> Documents/report.pdf
08:19:04 | Would move: photo1.jpg -> Images/photo1.jpg
08:19:04 | Would move: song.mp3 -> Audio/song.mp3
08:19:04 | Done. 3 files organized, 0 skipped.
08:19:04 | By category: Audio 1, Documents 1, Images 1.
```

## Features

- **Automatic classification** sorts files into Images, Documents, Videos, Audio, Archives, Code, and Other based on extension
- **Dry run mode** previews exactly what will move before anything actually happens, using `--dry-run`
- **Recursive mode** also organizes files in subdirectories with `--recursive`, while never descending into category folders or hidden folders
- **Hidden files are left alone** dotfiles such as `.env` are never moved, so config files stay where they are
- **Collision handling** renames a file if the destination filename already exists, such as `photo_1.jpg` or `photo_2.jpg`, instead of overwriting existing data
- **Exclude patterns** leave files matching a glob, such as `*.tmp`, exactly where they are with `--exclude`
- **Custom category rules** define your own extension to category mapping in a JSON file with `--config`, for example `{".nef": "Images"}`; your rules win over the built-in map
- **Undo** reverses the most recent run from its log file with `--undo`, moving files back to the target root under their original names
- **Logging** writes a timestamped `.log` file into the target directory so every move can be reviewed later
- **Run summary** `organize()` returns a dict with moved count, skipped count, dry run flag, and per-category counts under `by_category`, so scripts can check the result
- **Deterministic order** files are processed in sorted order, so the log and the summary come out the same way every time for the same directory
- **No external dependencies** uses only the Python standard library: `pathlib`, `shutil`, `argparse`, and `logging`

## Tech Stack

- Python 3.9+
- `pathlib` for modern object oriented path handling
- `shutil` for file move operations
- `argparse` for CLI argument parsing
- `logging` for console and file audit logging

## Getting Started

### Prerequisites

- Python 3.9 or higher. The project uses only the standard library, so no package installation is required.

### Installation

```bash
git clone https://github.com/MugdhoAI/file-organizer
cd file-organizer
```

### Usage

```bash
# Preview what would happen (recommended first run)
python main.py --path ~/Downloads --dry-run

# Actually organize the directory
python main.py --path ~/Downloads

# Also organize files in subdirectories
python main.py --path ~/Downloads --recursive

# Leave temp files and drafts where they are
python main.py --path ~/Downloads --exclude "*.tmp" --exclude "draft*"

# Use your own category rules from a JSON file
python main.py --path ~/Downloads --config rules.json

# Reverse the most recent run, using its log file
python main.py --path ~/Downloads --undo
```

A config file maps extensions to category names, for example:

```json
{".nef": "Images", ".blend": "Code"}
```

## Project Structure

```
file-organizer/
├── main.py              # CLI entry point, argument parsing, logging setup
├── src/
│   ├── classifier.py    # Decides which category a file belongs to
│   └── mover.py         # Handles file moves and collision handling
├── tests/
│   └── test_main.py     # Unit tests for classification and collision logic
└── .gitignore
```

## Running Tests

```bash
python -m unittest discover tests
```

The suite covers classification (including new extensions and case
insensitivity), collision numbering, live and dry run moves, hidden
file skipping, recursive mode, repeated runs in one process, sorted
run order, exclude patterns, custom category rules from a JSON config,
undo from the run log, and per-category summary counts.

## What I Learned

Separating "decide what should happen" in `classifier.py` from "actually do it" in `mover.py` made the dry run feature straightforward to implement. The same code path calculates the plan whether or not it executes it. I also learned the difference between catching a specific exception such as `PermissionError` and using a bare `except:`. The specific version lets me handle expected failures, such as a locked file, while allowing unexpected bugs to surface instead of hiding them.

## Future Improvements

- [x] User defined category rules via a JSON config file instead of hardcoded extensions
- [x] `--undo` flag that reverses the last run using the log file
- [x] Optional recursive mode for subdirectories
- [x] `--older-than` flag that only organizes files not modified recently

## Author

**Mugdho (All Asmaul Husnain)**

[GitHub](https://github.com/MugdhoAI) | [LinkedIn](https://linkedin.com/in/mugdhoai)
