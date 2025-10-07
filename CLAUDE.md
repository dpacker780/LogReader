# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LogReader is a cross-platform log file viewer that parses structured log files using ASCII field separator (char 31) format and provides real-time filtering, search, and clipboard copy functionality.

**Current Status**: The C++ version (built with C++17 and FTXUI) is the reference implementation.

**Active Development Goal**: Port the application to Python with PyQt6 as the GUI framework.

## Development Roadmap

### Phase I: Python Port (Current Phase)

**Objective**: Create a Python/PyQt6 version with feature parity to the C++ version.

**Setup Steps**:
1. Create local Python virtual environment (avoid using global Python installation)
2. Create `requirements.txt` with necessary dependencies (PyQt6, etc.)
3. Install required modules into the virtual environment
4. Port core functionality maintaining the same architecture patterns
5. Implement PyQt6 GUI matching the three-pane layout of the C++ version

**Key Python Port Considerations**:
- Use `threading` module for async parsing (equivalent to C++ `std::thread`)
- Use `threading.Lock` for synchronization (equivalent to C++ `std::mutex`)
- Implement QTableWidget or QTableView with virtualization for log display
- Use PyQt6 signals/slots for progress callbacks from parser thread
- Maintain the same log format specification (ASCII field separator char 31)

### Phase II: Feature Enhancements (Future)

After the Python port achieves feature parity, enhance the application based on user feedback from the C++ version.

## Python Development Setup

### Creating Virtual Environment (Windows)

```cmd
python -m venv venv
venv\Scripts\activate
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Running the Python Application

```bash
python src/main.py
```

### Deactivating Virtual Environment

```bash
deactivate
```

## C++ Version (Reference Implementation)

### Build Commands

**Windows (Visual Studio):**
```cmd
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

**Linux/macOS:**
```bash
mkdir build && cd build
cmake ..
make
```

### Running the C++ Application

```bash
./log_reader        # Linux/macOS
log_reader.exe      # Windows (from build/Release/ or build/Debug/)
```

## Log Format Specification

The parser expects log entries with ASCII field separator (char 31, `\x1F`) in this exact format:
```
timestamp<FS>LEVEL<FS>message<FS>source_file -> function(): line_number
```

Example:
```
16:29:40.318<FS>DEBUG<FS>Vulkan loader version: 1.4.304<FS>Vulkan.cpp -> initVulkan(): 92
```

Valid log levels: `DEBUG`, `INFO`, `WARN`, `ERROR`, `HEADER`, `FOOTER`

## Architecture

### Core Components (C++ Reference Implementation)

**LogEntry** (src/LogEntry.hpp)
- Header-only data structure defining `LogEntry` struct and `LogLevel` enum
- Single source of truth for log data representation
- **Python equivalent**: Use `dataclass` or `NamedTuple` with `Enum` for LogLevel

**LogParser** (src/LogParser.hpp, src/LogParser.cpp)
- Handles both synchronous (`parse()`) and asynchronous (`parseAsync()`) parsing
- Async parsing uses batched processing (5000 lines per batch) with mutex-protected writes
- Built-in progress callback mechanism for UI updates
- Thread-safe design with `std::atomic` flags for stopping/status checking
- **Python equivalent**: Use `threading.Thread`, `threading.Lock`, and `threading.Event` for thread control

**main.cpp** (src/main.cpp)
- Complete FTXUI-based TUI application with three-pane layout:
  1. File controls pane (top): File input, status display, Open/Copy buttons
  2. Log display pane (center): Virtualized scrollable table with filtering
  3. Search & filters pane (bottom): Search input and level checkboxes
- Uses FTXUI's component system with Container hierarchies for navigation
- Custom event handlers for scrolling (arrow keys, mouse wheel)
- **Python equivalent**: Use `QMainWindow` with `QVBoxLayout`, `QLineEdit`, `QTableView` with custom model, `QCheckBox` widgets

### Key Design Patterns

**Asynchronous Parsing Architecture:**
- Parser runs in separate thread (`parsing_thread`)
- Uses mutex-protected vector for concurrent log entry writes
- Progress callback posted as custom FTXUI events to trigger UI refresh
- Batched processing prevents UI blocking on large files

**Virtualized Rendering:**
- Only renders visible rows (max 45) from potentially large datasets
- Scroll position management with clamping (`scroll_y` variable in main.cpp:163)
- Reduces memory overhead for large log files

**Filter & Search Logic:**
- Filters applied by creating index vector (`filtered_indices`) instead of copying entries
- Search performed via simple substring match (`std::string::find()`)
- Level filters: OR logic when any checkbox is checked, show all when none checked

**Platform Abstraction:**
- Windows-specific: Console color enabling (main.cpp:32-45), clipboard via Win32 API
- Linux: Clipboard via xclip/xsel fallback
- Conditional compilation with `#ifdef _WIN32`

### File Structure

**C++ Version:**
```
src/
  LogEntry.hpp       - Data structures (header-only)
  LogParser.hpp      - Parser interface
  LogParser.cpp      - Parser implementation
  main.cpp           - FTXUI application and UI logic
```

**Python Version (Target Structure):**
```
src/
  log_entry.py       - LogEntry dataclass and LogLevel enum
  log_parser.py      - LogParser class with sync/async parsing
  main.py            - PyQt6 application entry point
  main_window.py     - Main window UI class
venv/                - Python virtual environment (git-ignored)
requirements.txt     - Python dependencies
```

### Threading Model

**C++ Version:**
- **Main thread**: Runs FTXUI event loop (`screen.Loop()`)
- **Parser thread**: Created by `parseAsync()`, writes to shared `log_entries` vector
- **Synchronization**: `std::mutex log_entries_mutex` protects shared state
- **Event posting**: `screen.PostEvent(Event::Custom)` triggers UI refresh from parser thread

**Python Version (Target):**
- **Main thread**: Runs PyQt6 event loop (`QApplication.exec()`)
- **Parser thread**: Created by `threading.Thread`, writes to shared list
- **Synchronization**: `threading.Lock` protects shared log entries list
- **Signal emission**: Use PyQt6 signals (custom `QObject` with `pyqtSignal`) to communicate from parser thread to GUI thread

## Important Implementation Details

1. **ASCII Field Separator Parsing**:
   - C++: Use char value 31 (`const char FIELD_SEPARATOR = 31`)
   - Python: Use `chr(31)` or `'\x1f'` for the field separator character
   - This is the core parsing strategy for performance (simple `split()` vs complex regex)

2. **Source Info Regex**: Pattern `R"((.*)\s*->\s*(.*)\(\):\s*(\d+))"` expects format: `filename -> function(): line_number`
   - Python equivalent: `r"(.*)\s*->\s*(.*)\(\):\s*(\d+)"`

3. **Configuration**: Last opened file path persisted to `logreader_config.txt` in working directory
   - Python: Use same approach with simple text file or consider JSON for future extensibility

4. **Debug Logging**:
   - C++: LogParser writes to `logreader_debug.log`
   - Python: Use Python's `logging` module with file handler

5. **UI Layout**:
   - C++: FTXUI Component Hierarchy with Container nesting
   - Python: PyQt6 layouts (`QVBoxLayout`, `QHBoxLayout`) with widget composition

6. **Thread Safety**: When modifying log display logic, always make a local copy of `log_entries` inside the lock to avoid holding the lock during rendering
   - This pattern should be maintained in the Python version

## Common Development Tasks

### Adding a New Log Level

1. Add enum value to `LogLevel` in src/LogEntry.hpp
2. Add parsing case in LogParser.cpp (two locations: `parse()` and `parseChunk()`)
3. Add display formatting in main.cpp: `LogLevelToString()` and `LogLevelToColor()`
4. Add checkbox to search/filters pane in main.cpp

### Modifying the Log Format

The field separator parsing logic is in two places (for sync and async):
- LogParser.cpp:70-84 (synchronous `parse()`)
- LogParser.cpp:229-239 (asynchronous `parseChunk()`)

Both must be kept in sync.

### Adding New Filter Types

Filtering logic is duplicated in two places in main.cpp:
1. Log renderer (main.cpp:354-372) - controls what's displayed
2. Copy button handler (main.cpp:212-228) - controls what's copied

Keep both in sync when adding new filters.

## Dependencies

### C++ Version
- **FTXUI v5.0.0**: Fetched automatically via CMake FetchContent
- **C++17 Standard Library**: `<filesystem>`, `<regex>`, `<thread>`, `<mutex>`, `<atomic>`

### Python Version (requirements.txt)
- **PyQt6**: Main GUI framework (~50MB)
- **PyQt6-Qt6**: Qt6 bindings (included with PyQt6)
- Consider adding for future enhancements:
  - `pyperclip`: Cross-platform clipboard support (alternative to PyQt6's clipboard)
  - `watchdog`: For potential file watching features in Phase II

## Platform-Specific Notes

### C++ Version
- **Windows**: Requires ENABLE_VIRTUAL_TERMINAL_PROCESSING for console colors (handled in main.cpp)
- **Windows**: Uses strcpy_s for clipboard operations
- **Linux/macOS**: Clipboard requires xclip or xsel installed on system

### Python Version
- **Cross-platform**: PyQt6 handles platform differences automatically
- **Clipboard**: Use `QApplication.clipboard()` for native clipboard access on all platforms
- **File paths**: Use `pathlib.Path` for cross-platform path handling

## Project Structure Notes

- The C++ source remains in `src/` as the reference implementation
- Python implementation should coexist in the same repository
- Use `.gitignore` to exclude:
  - `venv/` - Python virtual environment
  - `__pycache__/` - Python bytecode
  - `*.pyc` - Compiled Python files
  - `.pytest_cache/` - If tests are added
  - C++ build artifacts (`build/`, `out/`) are already ignored
