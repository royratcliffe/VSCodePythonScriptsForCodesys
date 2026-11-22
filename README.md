# CODESYS VS Code Python Utilities

A collection of Python and PowerShell utilities for working with CODESYS
exported project objects and Structured Text in Git repositories.

## Features

- Extract declarations and implementations from CODESYS `.object` JSON files
  into `.st` source files.
- Update matching CODESYS project objects from extracted Structured Text.
- Watch a project directory and refresh extracted source when objects change.
- Keep staged `.object` JSON files consistently formatted.
- Derive the project version from reachable Git release tags.
- Create GitHub releases from the version stored in the CODESYS project.
- Reformat all project objects with a PowerShell script.

## Requirements

- Python 3.9 or later
- Git
- GitHub CLI (`gh`) for release creation
- VS Code for the included task configuration
- CODESYS project objects exported beneath a `project` directory

The Python scripts use only the standard library.

## Project layout

By default, the scripts expect this layout:

```text
project/             CODESYS .object files
st/                  Extracted .st files
*.py                 Utility scripts
```

You can override the project and output directories on commands that support
those arguments.

## Usage

Run commands from the repository root.

### Extract Structured Text

```powershell
python extract_st.py
python extract_st.py path\to\project --output-dir path\to\st
```

Add `--stdout` to print extracted source without writing `.st` files.

### Update project objects

```powershell
python update_st.py --dry-run
python update_st.py
```

The update script matches `.st` files to project objects and validates section
labels before changing any object file.

### Watch for changes

```powershell
python watch_extract_st.py
python watch_extract_st.py project --output-dir st --poll-interval 0.5 --debounce 1
```

Press `Ctrl+C` to stop the watcher.

### Format project objects

Format every valid JSON object beneath `project`:

```powershell
.\Format-ObjectFiles.ps1 -Path project
```

Preview changes with:

```powershell
.\Format-ObjectFiles.ps1 -Path project -WhatIf
```

### Format staged objects before commits

The `pre-commit` script formats staged `.object` files and restages them. Enable
it with:

```powershell
git config core.hooksPath .
```

The hook file must use LF line endings. The `.gitattributes` configuration
enforces LF for repository text files.

### Update the project version

The release version is read from the nearest reachable release tag on the
current `HEAD` first-parent history. Supported tags use:

```text
vMajor.Minor.Patch
vMajor.Minor.Patch.Build
```

The unprefixed forms are also accepted.

```powershell
python update_version.py --dry-run
python update_version.py
```

The script requires full history and a reachable release tag. It writes the
derived `Major.Minor.Patch.Build` value to the CODESYS `Project Information`
object.

### Create a GitHub release

Authenticate GitHub CLI before using this command:

```powershell
gh auth login
```

Preview the release command without publishing or requiring a clean checkout:

```powershell
python create_release.py --dry-run
```

Create the release:

```powershell
python create_release.py
```

The checkout must be clean, the project information file must be tracked, and
the release tag must not already point to a different commit.

## VS Code tasks

The included `tasks.json` contains tasks for extraction, updates, formatting,
version updates, release creation, test execution, and hook installation. The
task commands expect this repository's utility scripts to remain in the
workspace root.

## Tests

Run the unit tests with:

```powershell
python -m unittest discover -v
```
