# LogReader Python Port Specification

## Project Goal

Port the LogReader application from C++/FTXUI to Python/PyQt6, maintaining feature parity with the original implementation while leveraging Python's strengths and PyQt6's rich GUI capabilities.

## Overview

This document specifies the requirements, architecture, and implementation plan for porting LogReader to Python with a PyQt6 GUI interface.

## Requirements

### Functional Requirements

#### Core Features (Must Have - Phase I)

1. **Log File Parsing**
   - Parse log files using ASCII field separator (char 31, `\x1f`)
   - Support log format: `timestamp<FS>LEVEL<FS>message<FS>source_file -> function(): line_number`
   - Support log levels: DEBUG, INFO, WARN, ERROR, HEADER, FOOTER
   - Asynchronous parsing with progress updates
   - Batch processing (5000 lines per batch) to prevent UI blocking

2. **Log Display**
   - Scrollable table/list view with columns: Timestamp, Level, Message, Source
   - Virtualized rendering for large log files (display only visible rows)
   - Color-coded log levels matching C++ version:
     - DEBUG: Cyan
     - INFO: Green
     - WARN: Yellow
     - ERROR: Red
     - HEADER/FOOTER: Blue
   - Display entry count: "Showing X of Y entries"

3. **Filtering**
   - Filter by log level (DEBUG, INFO, WARN, ERROR checkboxes)
   - Multiple filters can be active simultaneously (OR logic)
   - Show all entries when no filters are checked
   - Real-time filter application without re-parsing

4. **Search**
   - Text-based search through log messages
   - Case-sensitive substring matching
   - Combines with level filters (AND logic)
   - Real-time search without re-parsing

5. **File Management**
   - File path input field
   - "Open" button to trigger parsing
   - Remember last opened file path (persist to `logreader_config.txt`)
   - Load last file path on startup
   - Status message display (Ready, Parsing progress, Error messages)

6. **Clipboard Operations**
   - "Copy Filtered" button to copy currently filtered/searched entries to clipboard
   - Format: `[timestamp][LEVEL]: message | source_info`
   - Use native clipboard API (PyQt6's `QApplication.clipboard()`)

7. **User Interface**
   - Three-pane layout matching C++ version:
     - **Top pane**: File path input, Open button, Copy Filtered button, Status display
     - **Center pane**: Log entries table (scrollable, virtualized)
     - **Bottom pane**: Search input, Level filter checkboxes
   - Window title: "LogReader - Python"
   - Minimum window size: 1024x768
   - Resizable window with proper layout management

#### Non-Functional Requirements

1. **Performance**
   - Handle log files with 100,000+ entries
   - Maintain responsive UI during parsing (max 100ms UI freeze)
   - Filter/search updates within 200ms for 100k entries

2. **Cross-Platform**
   - Run on Windows, Linux, macOS without modifications
   - Use platform-agnostic file path handling (`pathlib.Path`)
   - Native look-and-feel on each platform (PyQt6 default)

3. **Code Quality**
   - Follow PEP 8 style guidelines
   - Type hints for all function signatures
   - Docstrings for all classes and public methods
   - Clear separation of concerns (parsing logic, data models, UI)

4. **Maintainability**
   - Modular architecture matching C++ design
   - No duplicated code between sync/async parsing
   - Easy to add new log levels or filters

## Architecture

### Component Design

#### 1. Data Model (`log_entry.py`)

```python
from dataclasses import dataclass
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    HEADER = "HEADER"
    FOOTER = "FOOTER"

@dataclass
class LogEntry:
    timestamp: str
    level: LogLevel
    message: str
    source_file: str
    source_function: str
    source_line: int
```

**Responsibilities:**
- Define log entry data structure
- Define log level enumeration
- No business logic (pure data container)

#### 2. Parser (`log_parser.py`)

```python
class LogParser:
    def __init__(self):
        self._parsing_active: bool = False
        self._stop_requested: threading.Event
        self._parser_thread: Optional[threading.Thread] = None

    def parse(self, file_path: str) -> List[LogEntry]:
        """Synchronous parsing - returns all entries at once"""
        pass

    def parse_async(self, file_path: str,
                   callback: Callable[[str, List[LogEntry]], None]) -> None:
        """Asynchronous parsing with progress callbacks"""
        pass

    def stop_parsing(self) -> None:
        """Request cancellation of async parsing"""
        pass

    def is_parsing(self) -> bool:
        """Check if async parsing is in progress"""
        pass
```

**Responsibilities:**
- Parse log files using ASCII field separator (char 31)
- Extract fields: timestamp, level, message, source info
- Parse source info regex: `(.*)\s*->\s*(.*)\(\):\s*(\d+)`
- Provide both sync and async parsing methods
- Batch processing (5000 lines/batch) in async mode
- Thread-safe operations with proper locking
- Progress callbacks: `callback(status_message, current_entries)`

**Implementation Notes:**
- Use `re.compile()` for source info regex (compile once, reuse)
- Use `threading.Thread` for async parsing
- Use `threading.Lock` to protect shared entry list
- Use `threading.Event` for stop signal
- Progress callback format: "Parsing... X% (Y lines)" or "Complete: X entries from Y lines"

#### 3. Main Window (`main_window.py`)

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # UI components
        self._file_input: QLineEdit
        self._open_button: QPushButton
        self._copy_button: QPushButton
        self._status_label: QLabel
        self._search_input: QLineEdit
        self._log_table: QTableView  # or QTableWidget
        self._filter_checkboxes: Dict[LogLevel, QCheckBox]

        # Data
        self._log_entries: List[LogEntry] = []
        self._entries_lock: threading.Lock
        self._parser: LogParser
```

**Responsibilities:**
- Create and layout all UI components
- Handle user interactions (button clicks, text input, checkbox changes)
- Coordinate between parser and UI
- Apply filters and search to log entries
- Update table view when data changes
- Manage configuration (load/save last file path)

**Key Methods:**
- `_setup_ui()`: Create and arrange widgets
- `_on_open_clicked()`: Start parsing
- `_on_copy_clicked()`: Copy filtered entries to clipboard
- `_on_search_changed()`: Update displayed entries
- `_on_filter_changed()`: Update displayed entries
- `_update_status(message: str)`: Update status label
- `_update_table()`: Refresh table with current filters/search
- `_parse_progress_callback(status: str, entries: List[LogEntry])`: Handle parser updates

**UI Layout:**
```
+---------------------------------------------------------------+
| File: [________________input_________________] [Open] [Copy]  |
| Status: Ready                                                 |
+---------------------------------------------------------------+
|                                                               |
| Timestamp   | Level  | Message              | Source         |
|-------------|--------|----------------------|----------------|
| 16:29:40.31 | DEBUG  | Vulkan loader...     | Vulkan.cpp:92  |
| 16:29:40.58 | INFO   | Supported...         | Vulkan.cpp:106 |
|                                                               |
|                      (scrollable)                             |
|                                                               |
| Showing 1,234 of 5,678 entries                                |
+---------------------------------------------------------------+
| Search: [______________search_input_______________]           |
| Filters: [ ] DEBUG  [ ] INFO  [ ] WARN  [ ] ERROR            |
+---------------------------------------------------------------+
```

#### 4. Table Model (`log_table_model.py`)

```python
class LogTableModel(QAbstractTableModel):
    """Custom table model for efficient log entry display"""

    def __init__(self):
        self._entries: List[LogEntry] = []
        self._filtered_indices: List[int] = []
```

**Responsibilities:**
- Implement Qt's Model/View pattern for efficient display
- Store references to log entries
- Maintain filtered indices (don't copy entries)
- Provide data to QTableView on demand
- Support color formatting per log level

**Implementation Notes:**
- Use `_filtered_indices` to avoid copying entries during filter/search
- Implement `rowCount()`, `columnCount()`, `data()`, `headerData()`
- Use `Qt.ForegroundRole` to return colors based on log level
- Call `beginResetModel()`/`endResetModel()` when data changes

#### 5. Application Entry Point (`main.py`)

```python
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LogReader")
    app.setOrganizationName("LogReader")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
```

**Responsibilities:**
- Initialize QApplication
- Create and show main window
- Start Qt event loop

#### 6. Configuration Manager (`config.py`)

```python
class ConfigManager:
    CONFIG_FILE = "logreader_config.txt"

    @staticmethod
    def load_last_file_path() -> str:
        """Load last opened file path, default to 'log.txt'"""
        pass

    @staticmethod
    def save_last_file_path(path: str) -> None:
        """Save file path to config file"""
        pass
```

**Responsibilities:**
- Load/save configuration to `logreader_config.txt`
- Provide default values when config doesn't exist
- Simple text file format (one line: file path)

### Threading Model

```
Main Thread (Qt Event Loop)
  |
  |- MainWindow (UI updates, user interactions)
  |    |
  |    |- Receives signals from parser thread
  |    |- Updates UI (table, status label)
  |    |- Applies filters/search (on main thread)
  |
  +- Parser Thread (created on "Open" click)
       |
       |- Reads file in batches
       |- Parses log entries
       |- Emits signals with progress updates
       |- Thread-safe writes to shared entry list (with lock)
```

**Thread Communication:**
- Use PyQt6 signals/slots (thread-safe by design)
- Create custom `QObject` with `pyqtSignal` for parser progress
- Alternative: Use `QMetaObject.invokeMethod()` with `Qt.QueuedConnection`

**Synchronization:**
- `threading.Lock` protects `_log_entries` list
- Parser thread: acquires lock, appends entries, releases lock
- Main thread: acquires lock, copies entries for display, releases lock
- Never hold lock during UI updates or heavy operations

### File Structure

```
LogReader/
├── src/                      # C++ source (existing)
│   ├── LogEntry.hpp
│   ├── LogParser.hpp
│   ├── LogParser.cpp
│   └── main.cpp
├── python/                   # New Python implementation
│   ├── log_entry.py          # Data models
│   ├── log_parser.py         # Parsing logic
│   ├── log_table_model.py    # Qt table model
│   ├── main_window.py        # Main window UI
│   ├── config.py             # Configuration management
│   └── main.py               # Application entry point
├── venv/                     # Virtual environment (gitignored)
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── CLAUDE.md                 # Development guidance
├── logreader_port.md         # This specification
├── CMakeLists.txt            # C++ build config
└── .gitignore                # Git ignore rules
```

## Implementation Plan

### Phase 1: Environment Setup

**Tasks:**
1. Create Python virtual environment
2. Create `requirements.txt` with PyQt6
3. Install dependencies
4. Verify PyQt6 installation with "Hello World" window

**Deliverable:** Working virtual environment with PyQt6 installed

**Acceptance Criteria:**
- `python -c "import PyQt6"` succeeds
- Simple PyQt6 window opens and closes

### Phase 2: Core Data Structures

**Tasks:**
1. Implement `log_entry.py` with `LogEntry` dataclass and `LogLevel` enum
2. Write unit tests for data structures
3. Implement `config.py` with load/save methods

**Deliverable:** Data models and configuration management

**Acceptance Criteria:**
- Can create LogEntry instances
- Can save/load file path from config file
- All tests pass

### Phase 3: Parser Implementation

**Tasks:**
1. Implement synchronous `parse()` method
2. Test with sample log files (existing C++ test files)
3. Implement asynchronous `parse_async()` method
4. Add threading, locking, and progress callbacks
5. Test async parsing with large files

**Deliverable:** Fully functional log parser

**Acceptance Criteria:**
- Successfully parses ASCII field separator format
- Correctly extracts all fields including source info regex
- Async parsing works without blocking
- Progress callbacks fire during parsing
- Can stop async parsing mid-operation
- Parses 100k line file in under 5 seconds

### Phase 4: Basic UI (No Data)

**Tasks:**
1. Implement `main.py` with QApplication setup
2. Implement `main_window.py` with all UI components
3. Create three-pane layout
4. Style components to match C++ version aesthetic
5. Test on Windows

**Deliverable:** Non-functional UI shell

**Acceptance Criteria:**
- Window opens with correct layout
- All widgets are present and arranged correctly
- Buttons don't crash when clicked (even if they do nothing)
- Window is resizable

### Phase 5: Table Model Implementation

**Tasks:**
1. Implement `log_table_model.py` with `QAbstractTableModel`
2. Implement required methods: `rowCount()`, `columnCount()`, `data()`, `headerData()`
3. Add color formatting for log levels
4. Test with mock data

**Deliverable:** Working table model

**Acceptance Criteria:**
- Can display log entries in table
- Columns show correct data
- Log levels have correct colors
- Table scrolls smoothly with 10k+ entries

### Phase 6: Integration

**Tasks:**
1. Connect parser to UI
2. Implement "Open" button functionality
3. Update table when parsing completes
4. Show progress updates in status label
5. Implement config load/save on startup/file open

**Deliverable:** Basic working application

**Acceptance Criteria:**
- Can open and parse a log file
- Entries appear in table with correct formatting
- Status shows progress during parsing
- Last file path is remembered between sessions

### Phase 7: Filtering and Search

**Tasks:**
1. Implement filter logic (level checkboxes)
2. Implement search logic (text input)
3. Update table model to use filtered indices
4. Show "X of Y entries" count
5. Ensure real-time updates

**Deliverable:** Filtering and search features

**Acceptance Criteria:**
- Checking level filters updates table immediately
- Typing in search updates table immediately
- Filters and search combine correctly (AND logic)
- Entry count is accurate
- Performance: Filter/search 100k entries in <200ms

### Phase 8: Clipboard Support

**Tasks:**
1. Implement "Copy Filtered" button
2. Format entries for clipboard
3. Use `QApplication.clipboard()` to copy text
4. Show success/failure in status label

**Deliverable:** Clipboard functionality

**Acceptance Criteria:**
- Copies currently filtered/searched entries
- Format matches C++ version
- Works on Windows (test Linux/macOS if available)
- Status message confirms copy success

### Phase 9: Polish and Testing

**Tasks:**
1. Add keyboard shortcuts (Ctrl+O for open, Ctrl+C for copy, Esc to clear search)
2. Add window icon
3. Handle edge cases (empty files, malformed lines, missing files)
4. Comprehensive testing with various log files
5. Performance testing with large files (100k+ lines)
6. Memory leak testing (open/close multiple large files)

**Deliverable:** Production-ready application

**Acceptance Criteria:**
- All features work as specified
- No crashes or errors with valid/invalid input
- Performance meets requirements
- No memory leaks during repeated operations

### Phase 10: Documentation

**Tasks:**
1. Add docstrings to all classes and public methods
2. Create Python-specific README section
3. Document any differences from C++ version
4. Create user guide if needed

**Deliverable:** Complete documentation

**Acceptance Criteria:**
- All code has proper docstrings
- README explains how to run Python version
- Known issues/differences are documented

## Testing Strategy

### Unit Tests
- `log_entry.py`: Test LogEntry creation, LogLevel enum
- `log_parser.py`: Test parsing with various log formats, edge cases
- `config.py`: Test save/load with various file states

### Integration Tests
- Parse real log files and verify entry count
- Test async parsing with progress callbacks
- Test filter/search combinations

### Manual Testing
- Open large log files (10k, 100k, 1M lines)
- Test all UI interactions
- Test on multiple platforms if possible
- Test with malformed log files

### Performance Benchmarks
- Parse 100k line file in <5 seconds
- Filter 100k entries in <200ms
- Search 100k entries in <200ms
- Memory usage <500MB for 1M entries

## Dependencies

### Python Version
- Python 3.9+ (for type hints, dataclasses)

### Required Packages (requirements.txt)
```
PyQt6>=6.6.0
```

### Optional Packages (for testing/development)
```
pytest>=7.4.0
pytest-qt>=4.2.0
black>=23.0.0
mypy>=1.5.0
```

## Success Criteria

The Python port is considered complete when:

1. **Feature Parity**: All features from C++ version work identically
2. **Performance**: Meets all performance benchmarks
3. **Cross-Platform**: Runs on Windows without issues (Linux/macOS bonus)
4. **Code Quality**: Passes linting, type checking, has proper documentation
5. **Stability**: No crashes, memory leaks, or data corruption with normal use
6. **User Experience**: UI is responsive and intuitive

## Future Enhancements (Phase II)

Ideas for post-port improvements (not required for Phase I):

- Export filtered logs to new file
- Regex search mode
- Timestamp range filtering
- Log level statistics/charts
- Multi-file support (tabs or file list)
- Dark mode theme
- Customizable colors per log level
- Column sorting
- Column resizing and reordering
- Jump to line number
- Bookmark entries
- Watch file for changes (live tail mode)
- Advanced filtering (AND/OR/NOT combinations)
- Search highlighting in message column

## Notes

- Maintain the same ASCII field separator format (char 31) for compatibility
- Keep the same config file name/format for easy migration
- The C++ version remains as reference implementation
- Both versions can coexist in the same repository
- Focus on code clarity and maintainability over micro-optimizations
- Use PyQt6's built-in capabilities (signals/slots) rather than reinventing patterns
