# File Organizer

A command line tool that automatically sorts files in a directory into category subfolders (Images, Documents, Videos, Audio, Archives, Code) based on file extension built for cleaning up folders like Downloads without doing it by hand.

## Demo

```
$ python main.py --path ~/Downloads --dry-run
08:19:04 | Starting organizer on /home/user/Downloads [DRY RUN]
08:19:04 | Would move: report.pdf -> Documents/report.pdf
08:19:04 | Would move: photo1.jpg -> Images/photo1.jpg
08:19:04 | Would move: song.mp3 -> Audio/song.mp3
08:19:04 | Done. 3 file(s) organized, 0 skipped.
```

## Features

- **Automatic classification** sorts files into Images, Documents, Videos, Audio, Archives, Code, and Other based on extension
- **Dry run mode** — preview exactly what will move before anything actually happens, using `--dry-run`
- **Collision safe** — if a destination filename already exists, the file is renamed (`photo_1.jpg`, `photo_2.jpg`, ...) instead of silently overwriting existing data
- **Logging** — every run writes a timestamped `.log` file into the target directory, so every move is auditable and traceable after the fact
- **Zero dependencies** — built entirely on the Python standard library (`pathlib`, `shutil`, `argparse`, `logging`); nothing to install

## Tech Stack

- Python 3.9+
- `pathlib` — modern, object-oriented path handling
- `shutil` — file move operations
- `argparse` — CLI argument parsing
- `logging` — dual console/file audit logging

## Getting Started

### Prerequisites
- Python 3.9 or higher (standard library only — no `pip install` required)

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
│   ├── classifier.py     # Decides which category a file belongs to
│   └── mover.py           # Handles the actual moving + collision-safe renaming
├── tests/
│   └── test_main.py       # Unit tests for classification and collision logic
└── .gitignore
```

## Running Tests
```bash
python -m unittest discover tests
```

## What I Learned

Separating "decide what should happen" (`classifier.py`) from "actually do it" (`mover.py`) made the dry run feature almost free to implement the same code path calculates the plan whether or not it executes it. I also learned the difference between catching a specific exception like `PermissionError` versus a bare `except:` the specific version lets me handle expected failures (a locked file) while letting unexpected bugs surface loudly instead of hiding silently.

## Future Improvements
- [ ] User defined category rules via a JSON config file, instead of hardcoded extensions
- [ ] `--undo` flag that reverses the last run using the log file
- [ ] Optional recursive mode for subdirectories

## Author
**Mugdho (All Asmaul Husnain)**
[GitHub](https://github.com/MugdhoAI) | [LinkedIn](https://linkedin.com/in/mugdhoai)
