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
```

## Features

- **Automatic classification** sorts files into Images, Documents, Videos, Audio, Archives, Code, and Other based on extension
- **Dry run mode** previews exactly what will move before anything actually happens, using `--dry-run`
- **Collision handling** renames a file if the destination filename already exists, such as `photo_1.jpg` or `photo_2.jpg`, instead of overwriting existing data
- **Logging** writes a timestamped `.log` file into the target directory so every move can be reviewed later
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

## What I Learned

Separating "decide what should happen" in `classifier.py` from "actually do it" in `mover.py` made the dry run feature straightforward to implement. The same code path calculates the plan whether or not it executes it. I also learned the difference between catching a specific exception such as `PermissionError` and using a bare `except:`. The specific version lets me handle expected failures, such as a locked file, while allowing unexpected bugs to surface instead of hiding them.

## Future Improvements

- [ ] User defined category rules via a JSON config file instead of hardcoded extensions
- [ ] `--undo` flag that reverses the last run using the log file
- [ ] Optional recursive mode for subdirectories

## Author

**Mugdho (All Asmaul Husnain)**

[GitHub](https://github.com/MugdhoAI) | [LinkedIn](https://linkedin.com/in/mugdhoai)
