# LogReader v1.0


![LogReader UI Screenshot](https://github.com/dpacker780/LogReader/blob/master/logreader_UI.png)

**A modern, professional GUI log viewer built with Python and PyQt6.**

Cross-platform log file viewer with real-time filtering, search, and navigation capabilities.

> **Note**: This is a Python rewrite of the original C++ terminal version. The C++ version is available in a separate repository for terminal-only environments.

---

## Features

- **Native File Dialog**: Standard file picker with last directory memory
- **Professional Status Bar**: Real-time status, file info, entry counts, and line navigation
- **Line Numbers**: Reference specific log entries easily with original file line numbers
- **Jump to Line**: Navigate directly to any line number with auto-filter clearing
- **Fast Log Parsing**: Async parsing with progress updates (handles 100k+ entries smoothly)
- **Real-time Filtering**: Filter by log levels (DEBUG, INFO, WARN, ERROR) without re-parsing
- **Instant Search**: Search through log messages with live results
- **Color-Coded Levels**: Visual distinction between log severity levels
- **Row Selection**: Select single or multiple rows with Ctrl+C to copy
- **Keyboard Shortcuts**: Efficient workflow with Ctrl+O, Ctrl+R, Ctrl+C, Esc, Ctrl+Q
- **Persistent Configuration**: Remembers last directory and file

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PyQt6

### Installation

#### Step 1: Verify Python Installation

```bash
# Check Python version (must be 3.10+)
python --version

# If not installed, download from python.org
```

#### Step 2: Set Up Virtual Environment

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
```

#### Step 3: Install Dependencies

```bash
# Install PyQt6 and other requirements
pip install -r requirements.txt

# Verify installation
pip list | grep PyQt6
```

### Running the Application

```bash
python python/main.py
```

## Usage Guide

For detailed usage instructions, see [USER_GUIDE.md](USER_GUIDE.md).

### Quick Start Guide

#### Opening Files

1. **File → Open** or press **Ctrl+O**
2. Select a `.log` file in the file dialog
3. Entries load automatically with progress updates

#### Navigating Logs

- **Scroll**: Mouse wheel or scroll bar
- **Select Rows**: Click to select, Shift+Click for range, Ctrl+Click for multi-select
- **Copy**: Select rows and press **Ctrl+C** to copy to clipboard
- **Jump to Line**: Enter line number in "Jump to Line" field and press Enter or click "Go"

#### Filtering and Search

- **Level Filters**: Check boxes to show only specific log levels (OR logic)
- **Search**: Type in search box to filter by message content (AND logic with level filters)
- **Clear Filters**: Click "Esc" in search box or use "Jump to Line" (auto-clears)

#### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+O** | Open file dialog |
| **Ctrl+R** | Reload current file |
| **Ctrl+C** | Copy selected rows to clipboard |
| **Ctrl+Q** | Quit application |
| **Esc** | Clear search box |
| **Enter** | (in Jump to Line field) Jump to line |

#### Status Bar Information

The status bar at the bottom shows:
- **Left**: Current operation status (Ready, Parsing, Complete, Errors)
- **Center-Left**: Current file name
- **Center-Right**: Entry count (total and visible after filtering)
- **Right**: Line navigation info (reserved for future features)

### Log Format

The parser expects log entries using ASCII field separators (character 31):

```
timestamp<FS>LEVEL<FS>message<FS>source_file -> function(): line_number
```

Where `<FS>` represents the ASCII field separator (char 31).

**Example:**
```
16:29:40.318<FS>DEBUG<FS>Vulkan loader version: 1.4.304<FS>Vulkan.cpp -> initVulkan(): 92
16:29:40.587<FS>INFO<FS>Supported instance extensions:<FS>Vulkan.cpp -> initVulkan(): 106
16:29:40.629<FS>ERROR<FS>Failed to create surface<FS>Vulkan.cpp -> createSurface(): 156
```

### Architecture

- **python/main.py** - Application entry point
- **python/main_window.py** - Main UI window (PyQt6)
- **python/log_parser.py** - Async log file parser with batching
- **python/log_table_model.py** - Qt Model/View for efficient display
- **python/log_entry.py** - Data models (LogEntry, LogLevel)
- **python/config.py** - Configuration persistence

### Performance

- **Parsing**: ~4,400 entries/sec on typical hardware
- **Filtering**: <1ms for 1,000+ entries
- **Async Design**: UI remains responsive during large file loads
- **Memory Efficient**: Uses filtered indices instead of copying entries

---

## Log Format Details

LogReader uses an efficient ASCII field separator format:

- **Faster parsing**: Simple field splitting vs complex regex matching
- **More reliable**: Eliminates ambiguity when log messages contain special characters
- **Better performance**: Handles large log files more efficiently
- **Cleaner data**: No escaping needed for brackets, colons, or pipes in log messages

---

## Roadmap

### Future Enhancements (v1.1+)

- Recent files list (File → Recent)
- Bookmarks for important lines
- Split view (compare two log files)
- Export filtered results
- Dark mode theme
- Column sorting
- Custom column ordering
- Live tail mode (watch file for changes)
- Log level statistics
- Timeline visualization

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Version History

### v1.0 (Python GUI) - 2025
- Initial PyQt6 GUI release
- Native file dialog with directory memory
- Professional status bar
- Line numbers column
- Jump to line feature
- Async parsing with progress
- Complete feature parity with C++ version plus enhancements

### v0.x (C++ Terminal)
- Original FTXUI terminal implementation
- Basic filtering and search
- Cross-platform support
