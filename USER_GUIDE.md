# LogReader Python v1.0 - User Guide

Complete guide to using LogReader, a modern GUI log viewer built with Python and PyQt6.

---

## Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [User Interface Overview](#user-interface-overview)
4. [Features & Usage](#features--usage)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Tips & Tricks](#tips--tricks)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 512MB minimum (2GB+ recommended for large log files)
- **Disk Space**: ~50MB for application and dependencies

### Step 1: Install Python

#### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```

#### macOS

```bash
# Using Homebrew (recommended)
brew install python@3.10

# Verify installation
python3 --version
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Verify installation
python3 --version
```

### Step 2: Set Up LogReader

```bash
# Navigate to LogReader directory
cd /path/to/LogReader

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Run the application
python python/main.py
```

You should see the LogReader window open. If you encounter errors, see [Troubleshooting](#troubleshooting).

---

## Getting Started

### Opening Your First Log File

1. Launch LogReader: `python python/main.py`
2. Press **Ctrl+O** or click **File → Open**
3. Navigate to your log file (`.log` extension)
4. Click **Open**
5. Watch the progress in the status bar as the file loads

### Understanding the Interface

The LogReader window has three main sections:

1. **Menu Bar** (top): File and Help menus
2. **Log Display** (center): Table showing log entries
3. **Search & Filters** (bottom): Controls for filtering and navigation
4. **Status Bar** (bottom): Real-time information

---

## User Interface Overview

### Menu Bar

#### File Menu
- **Open... (Ctrl+O)**: Open a log file
- **Reload (Ctrl+R)**: Reload the current file
- **Quit (Ctrl+Q)**: Exit the application

#### Help Menu
- **Tag Colors**: Shows log level color legend
- **Keyboard Shortcuts**: Lists all available shortcuts

### Log Display Table

Five columns display log entry information:

| Column | Description | Width |
|--------|-------------|-------|
| **Line #** | Original file line number (1-based) | 70px |
| **Timestamp** | When the log entry was created | 120px |
| **Level** | Log severity (color-coded) | 80px |
| **Message** | The log message content | Flexible |
| **Source** | Source file, function, and line | 250px |

#### Color Coding

Log levels are color-coded for quick identification:

- **DEBUG**: Cyan
- **INFO**: Green
- **WARN**: Yellow
- **ERROR**: Red
- **HEADER**: Blue
- **FOOTER**: Blue

### Search & Filters Panel

#### Search Box
- Type to filter log messages in real-time
- Case-insensitive substring matching
- Works with level filters (AND logic)
- Press **Esc** to clear

#### Jump to Line
- Enter a line number (from the Line # column)
- Press **Enter** or click **Go**
- Automatically clears filters to show the target line

#### Level Filter Checkboxes
- **DEBUG**: Development/diagnostic messages
- **INFO**: Informational messages
- **WARN**: Warning messages
- **ERROR**: Error messages

Check multiple boxes to show multiple levels (OR logic).

### Status Bar

Displays four sections of information:

1. **Status Message** (left): Current operation
   - "Ready" - Idle, waiting for action
   - "Parsing... 45%" - Loading file with progress
   - "Complete: 1,271 entries from 1,369 lines" - Parse finished
   - "Jumped to line 42" - Navigation feedback
   - Error messages when issues occur

2. **File Info** (center-left): Currently loaded file
   - "No file loaded" - No file open
   - "File: helix.log" - Current file name

3. **Entry Count** (center-right): Number of entries
   - "1,271 entries" - All entries shown
   - "1,271 entries (326 visible)" - After filtering

4. **Line Info** (right): Reserved for future features

---

## Features & Usage

### 1. Opening Files

**Method 1: File Dialog (Recommended)**
1. Press **Ctrl+O** or **File → Open**
2. Browse to your log file
3. Click **Open**

**Method 2: Recent Directory**
- LogReader remembers the last directory you used
- The file dialog opens to that location automatically

**Supported File Types:**
- `.log` files (recommended)
- All files (`*.*`)

### 2. Filtering Logs

#### By Log Level

1. Check the log level boxes you want to see
2. Table updates instantly
3. Multiple selections use OR logic (show DEBUG OR INFO)

**Example:** To see only errors and warnings:
- Uncheck DEBUG and INFO
- Check WARN and ERROR

#### By Search Text

1. Type in the Search box
2. Table updates as you type
3. Case-insensitive matching
4. Searches only the Message column

**Example:** To find Vulkan-related logs:
- Type "vulkan" in search box
- All entries containing "vulkan" (case-insensitive) will show

#### Combined Filtering

Search and level filters work together (AND logic):

**Example:** To find ERROR messages about "failed":
1. Check only ERROR in filters
2. Type "failed" in search box
3. Result: Only ERROR entries containing "failed"

### 3. Navigating Logs

#### Scrolling
- **Mouse Wheel**: Scroll up/down
- **Scroll Bar**: Drag or click
- **Keyboard**: Arrow keys (when table has focus)

#### Selecting Rows
- **Single Row**: Click anywhere on the row
- **Multiple Rows**: Ctrl+Click individual rows
- **Range**: Shift+Click to select range
- Selected rows are highlighted

#### Jumping to Specific Lines

1. Find the line number you want (from Line # column or external reference)
2. Enter it in "Jump to Line:" field
3. Press **Enter** or click **Go**

**What happens:**
- All filters and search clear automatically
- The target row is selected
- The view scrolls to center on that row
- Status bar confirms: "Jumped to line 42"

**Error Handling:**
- Invalid input: "Error: Invalid line number 'abc'"
- Line not found: "Error: Line 99999 not found"
- Negative/zero: "Error: Line number must be positive"

### 4. Copying Log Entries

1. Select one or more rows (click, Ctrl+Click, Shift+Click)
2. Press **Ctrl+C**
3. Paste into any text editor

**Format:** Each entry is formatted as:
```
[timestamp][LEVEL  ]: message | source_file -> function(): line
```

**Example:**
```
[16:29:40.318][DEBUG  ]: Vulkan loader version: 1.4.304 | Vulkan.cpp -> initVulkan(): 92
[16:29:40.587][INFO   ]: Supported instance extensions: | Vulkan.cpp -> initVulkan(): 106
```

### 5. Reloading Files

Use **Ctrl+R** or **File → Reload** when:
- The log file has been updated externally
- You want to refresh the current view
- Filters remain active after reload

---

## Keyboard Shortcuts

### File Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| **Ctrl+O** | Open | Open file dialog to select log file |
| **Ctrl+R** | Reload | Reload current log file |
| **Ctrl+Q** | Quit | Exit LogReader |

### Editing & Navigation

| Shortcut | Action | Description |
|----------|--------|-------------|
| **Ctrl+C** | Copy | Copy selected rows to clipboard |
| **Esc** | Clear Search | Clear the search input field |
| **Enter** | Jump | (in Jump to Line field) Navigate to line |

### Table Navigation

| Shortcut | Action | Description |
|----------|--------|-------------|
| **↑/↓** | Scroll | Scroll up/down one entry |
| **Page Up/Down** | Page Scroll | Scroll one page |
| **Home/End** | Jump | Jump to first/last entry |
| **Click** | Select | Select single row |
| **Shift+Click** | Range Select | Select range of rows |
| **Ctrl+Click** | Multi-Select | Add/remove from selection |

---

## Tips & Tricks

### 1. Fast Workflow

**Typical debugging session:**
1. **Ctrl+O** - Open log file
2. Check **ERROR** - Focus on errors first
3. Type "failed" in search - Find specific failures
4. Note line numbers from Line # column
5. Share line numbers with team: "Check line 1042"
6. **Ctrl+C** - Copy relevant entries
7. Paste into bug report

### 2. Finding Related Logs

1. Find an error entry
2. Note its timestamp
3. Clear filters (**Esc** in search, uncheck all filters)
4. Look at surrounding lines for context

### 3. Comparing Log Levels

1. Check **DEBUG** only - See detailed flow
2. Check **INFO** only - See high-level operations
3. Check **WARN** + **ERROR** - See all issues

### 4. Quick Line References

When discussing logs with teammates:
- "Line 1042 shows the crash"
- "Check lines 500-520 for the API calls"
- Jump to line feature makes verification instant

### 5. Performance Tips

For very large files (100k+ entries):
- Let the file load completely before filtering
- Use level filters before search (narrows results faster)
- Close other applications if memory is limited

---

## Troubleshooting

### Application Won't Start

**Error: "python: command not found"**
- **Solution**: Python not installed or not in PATH
- **Fix**: Reinstall Python with "Add to PATH" option checked

**Error: "No module named 'PyQt6'"**
- **Solution**: PyQt6 not installed
- **Fix**:
  ```bash
  pip install -r requirements.txt
  ```

**Error: Virtual environment not activated**
- **Solution**: Dependencies installed globally or not at all
- **Fix**: Activate venv first:
  ```bash
  # Windows:
  venv\Scripts\activate
  # macOS/Linux:
  source venv/bin/activate
  ```

### File Won't Open

**Error: "File not found"**
- **Solution**: File moved or deleted
- **Fix**: Use **Ctrl+O** to browse to current location

**Error: "Parsing failed"**
- **Solution**: File not in expected format
- **Fix**: Verify file uses ASCII field separator format (char 31)

**No entries show after parsing**
- **Solution**: File format doesn't match expected structure
- **Fix**: Check log format section in README.md

### Performance Issues

**Slow loading large files**
- **Normal**: Files over 50MB take time
- **Tip**: Watch progress bar in status bar
- **Issue**: If frozen for >30 seconds, may be out of memory

**UI freezes during filtering**
- **Rare**: Usually filtering is <1ms
- **Fix**: Try reloading the file (**Ctrl+R**)

### Display Issues

**Columns too narrow/wide**
- **Solution**: Drag column borders in header
- **Fix**: Restart application to reset to defaults

**Colors not showing**
- **Solution**: Level column should show colors
- **Fix**: Check if you're filtering - only shown levels have colors

**Text too small/large**
- **Current**: Fixed at 9pt Consolas/Courier New
- **Future**: Font size preferences coming in v1.1

### Jump to Line Issues

**"Line not found" but line exists in file**
- **Check**: Line # column value (may differ from file line if some lines didn't parse)
- **Fix**: Use the Line # shown in the table, not the text editor line number

### Other Issues

**Search not finding text**
- **Check**: Search is case-insensitive but exact substring
- **Tip**: Try shorter search terms
- **Example**: "vulkan" finds "Vulkan loader" but "loader vulkan" does not

**Can't copy selected rows**
- **Check**: Rows actually selected (highlighted)?
- **Fix**: Click on row first, then **Ctrl+C**

---

## Getting Help

### Check Documentation
- **README.md** - Installation and features overview
- **USER_GUIDE.md** (this file) - Detailed usage instructions
- **logreader_improvements.md** - Technical specification

### Report Issues

When reporting bugs, please include:
1. Operating system and version
2. Python version (`python --version`)
3. PyQt6 version (`pip show PyQt6`)
4. Log file size and entry count
5. Steps to reproduce the issue
6. Error messages or screenshots

### Feature Requests

See **Roadmap** section in README.md for planned features. For other requests, please open an issue on GitHub.

---

## Next Steps

- Explore the keyboard shortcuts to speed up your workflow
- Try the Jump to Line feature for quick navigation
- Experiment with combined filters and search
- Check out the roadmap for upcoming features

**Happy log hunting!** 🔍
