# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LogReader v1.0** is a modern, professional GUI log viewer built with Python and PyQt6. It parses structured log files using ASCII field separator (char 31) format and provides real-time filtering, search, navigation, and copy functionality.

**This is the Python/PyQt6 implementation.** The original C++ terminal version is maintained in a separate repository (`LogReader-Terminal`) and is no longer actively developed.

## Quick Start

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
python python/main.py
```

### Testing

```bash
# Integration test with auto-load
python python/test_integration.py

# Filter/search performance tests
python python/test_filter_search.py

# Parser unit tests
python python/test_parser.py
```

## Architecture

### Core Components

**python/main.py** (50 lines)
- Application entry point
- Creates QApplication and MainWindow
- Sets up high DPI scaling
- Version: 1.0

**python/main_window.py** (750+ lines)
- Main UI window with PyQt6
- Three-pane layout: Log Display (center), Search/Filters (bottom), Status Bar (bottom)
- File dialog for opening files (Ctrl+O)
- Async parsing with progress updates
- Real-time filtering and search
- Multi-row selection with Ctrl+C copy
- Jump to line feature
- Help menu with Tag Colors, Keyboard Shortcuts, and About dialogs

**python/log_parser.py** (305 lines)
- LogParser class with sync and async parsing
- Async: Spawns background thread, batches 5,000 lines at a time
- Thread-safe with mutex-protected log entry list
- Progress callbacks via function parameter
- Tracks line numbers (1-based) for jump-to-line feature
- ASCII field separator parsing (char 31)

**python/log_table_model.py** (230 lines)
- QAbstractTableModel for efficient display
- 5 columns: Line #, Timestamp, Level, Message, Source
- Color-coded log levels (DEBUG=Cyan, INFO=Green, WARN=Yellow, ERROR=Red)
- Filtered indices (no entry copying, memory efficient)
- Virtualized rendering (only visible rows)

**python/log_entry.py** (197 lines)
- LogEntry dataclass with fields: timestamp, level, message, source_file, source_function, source_line, line_number
- LogLevel enum: DEBUG, INFO, WARN, ERROR, HEADER, FOOTER
- to_clipboard_format() method for Ctrl+C copy
- format_source_info() for table display

**python/config.py** (135 lines)
- ConfigManager for persistence
- Saves last directory and file path (two-line format)
- Simple text file: logreader_config.txt
- Backward compatible with old single-line format

### File Structure

```
LogReader/
├── python/
│   ├── main.py              # Entry point
│   ├── main_window.py       # Main UI (750+ lines)
│   ├── log_parser.py        # Parser (305 lines)
│   ├── log_table_model.py   # Qt Model/View (230 lines)
│   ├── log_entry.py         # Data models (197 lines)
│   ├── config.py            # Configuration (135 lines)
│   └── test_*.py            # Test files (8 files)
├── venv/                    # Virtual environment (git-ignored)
├── requirements.txt         # PyQt6>=6.6.0
├── README.md                # Main documentation
├── USER_GUIDE.md            # Comprehensive user guide
├── GETTING_STARTED.md       # Quick setup guide
├── RELEASE_v1.0.md          # Release notes
├── CHANGELOG.md             # Version history
├── logreader_improvements.md # UI improvements spec
└── logreader_port.md        # Original port spec
```

## Log Format Specification

The parser expects log entries with ASCII field separator (char 31, `\x1F`) in this format:

```
timestamp<FS>LEVEL<FS>message<FS>source_file -> function(): line_number
```

**Example:**
```
16:29:40.318<FS>DEBUG<FS>Vulkan loader version: 1.4.304<FS>Vulkan.cpp -> initVulkan(): 92
16:29:40.587<FS>INFO<FS>Supported instance extensions:<FS>Vulkan.cpp -> initVulkan(): 106
16:29:40.629<FS>ERROR<FS>Failed to create surface<FS>Vulkan.cpp -> createSurface(): 156
```

**Valid log levels**: DEBUG, INFO, WARN, ERROR, HEADER, FOOTER

**Field separator**: `chr(31)` or `'\x1f'` in Python

## Key Features (v1.0)

### UI Features
- **Native File Dialog**: QFileDialog with last directory memory (Ctrl+O)
- **Status Bar**: 4 sections (status | file | entries | line info)
- **Line Numbers**: Original file line numbers in first column
- **Jump to Line**: Navigate to specific line with auto-filter clear
- **Color-Coded Levels**: Visual distinction for log severity
- **Multi-Row Selection**: Ctrl+Click, Shift+Click, Ctrl+C to copy
- **Keyboard Shortcuts**: Ctrl+O, Ctrl+R, Ctrl+C, Ctrl+Q, Esc

### Core Features
- **Async Parsing**: Background thread, 5,000 line batches, progress updates
- **Real-Time Filtering**: By log level (OR logic)
- **Instant Search**: Substring match in message field (AND logic with filters)
- **Reload**: Ctrl+R to refresh current file
- **Configuration**: Persists last directory and file

### Help Menu
- **Tag Colors**: Color legend for log levels
- **Keyboard Shortcuts**: Complete shortcut reference
- **About LogReader**: Version, license, features, copyright

## Threading Model

### Main Thread (PyQt6 Event Loop)
- Runs `QApplication.exec()`
- Handles all UI updates and user interactions
- Receives signals from parser thread

### Parser Thread (Background)
- Created by `threading.Thread` in `parse_async()`
- Reads file in batches (5,000 lines)
- Writes to shared `log_entries` list (mutex-protected)
- Calls progress callback with status and entries

### Thread Safety
- **Mutex**: `threading.Lock` protects `log_entries` list
- **Signals**: `ParserSignals` (QObject with pyqtSignal) for thread-safe UI updates
- **Stop Flag**: `threading.Event` for canceling parse

**Pattern:**
```python
with self._entries_lock:
    # Access log_entries safely
    entries_copy = self._log_entries.copy()
# Use entries_copy outside lock
```

## Common Development Tasks

### Adding a New Log Level

1. Add to LogLevel enum in `python/log_entry.py`:
   ```python
   class LogLevel(Enum):
       TRACE = "TRACE"  # New level
   ```

2. Add color in `python/log_table_model.py`:
   ```python
   LEVEL_COLORS = {
       LogLevel.TRACE: QColor(128, 128, 255),  # Light blue
   }
   ```

3. Add checkbox in `python/main_window.py` (`_create_search_filter_pane`):
   ```python
   for level in [LogLevel.TRACE, LogLevel.DEBUG, ...]:
   ```

### Modifying the Log Format

Update parsing in `python/log_parser.py`:
- `_parse_line()` method (line ~234) - handles both sync and async
- Field separator: `self.FIELD_SEPARATOR = chr(31)`
- Source info regex: `r"(.*)\s*->\s*(.*)\(\):\s*(\d+)"`

### Adding New Filters

Update filtering logic in `python/main_window.py`:
- `_apply_filters()` method (line ~458) - controls what's displayed
- Uses filtered indices, not entry copying
- OR logic for level filters, AND logic for search

### Updating the UI

**Main window layout** (`python/main_window.py`):
- `_setup_ui()` - Creates three-pane layout
- `_create_log_display_pane()` - Center table
- `_create_search_filter_pane()` - Bottom controls
- `_setup_statusbar()` - Bottom status bar

**Table model** (`python/log_table_model.py`):
- `data()` - Returns cell content, colors, alignment
- `headerData()` - Column headers
- Column indices: COL_LINE_NUMBER=0, COL_TIMESTAMP=1, COL_LEVEL=2, COL_MESSAGE=3, COL_SOURCE=4

### Adding Menu Items

In `python/main_window.py`, `_setup_menubar()`:
```python
# Add to File menu
action = QAction("&New Feature", self)
action.setShortcut(QKeySequence("Ctrl+N"))
action.triggered.connect(self._on_new_feature)
file_menu.addAction(action)
```

## Performance Characteristics

- **Parsing**: ~4,400 entries/sec on typical hardware
- **Filtering**: <1ms for 1,000+ entries (uses index list, no copying)
- **Memory**: Efficient with filtered indices (1 list vs 2 lists)
- **UI Responsiveness**: Async parsing, batched updates, virtualized rendering

## Configuration

**File**: `logreader_config.txt` (user's working directory)

**Format** (two lines):
```
/path/to/last/directory
/path/to/last/directory/file.log
```

**Backward compatibility**: Single-line format (just file path) still works, directory extracted automatically.

## Dependencies

**requirements.txt**:
```
PyQt6>=6.6.0
```

**Standard Library**:
- threading: Thread, Lock, Event
- pathlib: Path (cross-platform paths)
- dataclasses: @dataclass decorator
- enum: Enum class
- re: Regular expressions
- typing: Type hints

## Testing

### Test Files

**python/test_integration.py**
- Full application test
- Auto-loads helix.log or test_input.log
- Simulates user workflow

**python/test_filter_search.py**
- Filter and search logic tests
- Performance benchmarks
- Validates OR/AND logic

**python/test_parser.py**
- Parser unit tests
- Line number tracking
- Edge cases

**Other test files**:
- test_data_structures.py - LogEntry tests
- test_table_model.py - Qt model tests
- test_main_window_with_data.py - UI with mock data
- test_pyqt.py - PyQt6 installation check

### Sample Log Files

- **helix.log** (192 KB, 1,369 lines) - Real-world example
- **test_input.log** (192 KB) - Duplicate for testing
- **test_ascii_format.log** (162 bytes) - Minimal test
- **test_new_format.log** (270 bytes) - Format validation

## Platform Support

**Tested**:
- Windows 10/11 (Python 3.10.10, PyQt6 6.9.1)

**Supported** (needs community testing):
- macOS 10.14+ (Python 3.10+, PyQt6 6.6.0+)
- Linux (Ubuntu 20.04+, Python 3.10+, PyQt6 6.6.0+)

**Cross-platform handled by PyQt6**:
- File dialogs (QFileDialog)
- Clipboard (QApplication.clipboard())
- Keyboard shortcuts (QKeySequence)
- High DPI scaling (automatic)

## Git Workflow

**Branch**: master

**Commit Style**:
```
Brief description (imperative mood)

Detailed explanation of changes:
- Feature 1
- Feature 2

Technical details, rationale, or migration notes if needed.
```

**Current commits**:
```
9d31582 Add About dialog and update window title
d839f20 Initial commit - LogReader v1.0 (Python/PyQt6)
```

## Version Information

**Current Version**: 1.0

**Version Location**:
- `python/main.py` - `__version__ = "1.0"`
- Help → About LogReader dialog
- CHANGELOG.md

**Window Title**: "LogReader" (no version number)

## Documentation

**For Users**:
- **README.md** - Quick start, features, installation
- **GETTING_STARTED.md** - 5-minute setup guide
- **USER_GUIDE.md** - Comprehensive manual (400+ lines)

**For Developers**:
- **CLAUDE.md** (this file) - Development guide
- **logreader_improvements.md** - UI improvements spec (Changes A-D)
- **logreader_port.md** - Original port specification (Phases 1-10)

**For Release**:
- **RELEASE_v1.0.md** - Release notes with feature comparison
- **CHANGELOG.md** - Version history (Keep a Changelog format)
- **LICENSE** - MIT License

## Future Roadmap

### v1.1 (Planned - Q2 2025)
- Recent files list (File → Recent)
- User preferences (font size, theme)
- Dark mode support
- Column sorting
- Export filtered results

### v1.2 (Planned - Q3 2025)
- Live tail mode (watch file changes)
- Bookmarks for important lines
- Split view (compare two files)
- Log level statistics
- Timeline visualization

### v2.0 (Planned - Q4 2025)
- Plugin system
- Custom parsers
- Advanced search (regex, multi-field)
- Session management
- Log correlation features

## Original C++ Version

The original C++ terminal version (FTXUI-based) is now in a separate repository: `LogReader-Terminal`

**Not actively maintained.** This Python version is recommended for:
- Active development and bug fixes
- New features
- Better user experience
- Easier installation and cross-platform support

The C++ version remains available for terminal-only environments.

## Contact & Contributing

**Repository**: LogReader (Python/PyQt6 version)

**Contributing**:
- Report bugs via GitHub Issues
- Feature requests via GitHub Discussions
- Pull requests welcome (follow existing code style)
- Test on macOS/Linux appreciated

**Code Style**:
- Follow PEP 8
- Type hints preferred
- Docstrings for all public methods
- Comments for complex logic

---

**Happy coding!** This is a clean, well-documented Python project ready for enhancement and maintenance.
