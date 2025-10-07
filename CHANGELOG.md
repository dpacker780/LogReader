# Changelog

All notable changes to LogReader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0] - 2025-01-07

### Added - Python GUI Version

#### Core Features
- **Native GUI Interface**: Complete PyQt6-based graphical user interface
- **File Dialog**: Native OS file picker with last directory memory (Ctrl+O)
- **Status Bar**: Professional 4-section status bar (status | file | entries | line)
- **Line Numbers**: Original file line numbers shown in dedicated first column
- **Jump to Line**: Navigate to specific line numbers with auto-filter clearing
- **Reload**: Refresh current file with Ctrl+R hotkey
- **Menubar**: File and Help menus with standard shortcuts

#### User Experience
- **Async Parsing**: Background parsing with real-time progress updates
- **Multi-Select**: Select multiple rows with Ctrl+Click and Shift+Click
- **Copy to Clipboard**: Ctrl+C to copy selected rows in formatted text
- **Color-Coded Levels**: Visual log level distinction (DEBUG=Cyan, INFO=Green, WARN=Yellow, ERROR=Red)
- **Keyboard Shortcuts**: Ctrl+O (Open), Ctrl+R (Reload), Ctrl+C (Copy), Ctrl+Q (Quit), Esc (Clear Search)
- **Help Dialogs**: Tag Colors and Keyboard Shortcuts reference

#### Technical
- **Performance**: ~4,400 entries/sec parsing, <1ms filtering for 1,000+ entries
- **Memory Efficient**: Uses filtered indices instead of copying entries
- **Thread Safe**: Mutex-protected data access with Qt signals/slots
- **Batched Processing**: 5,000 lines per batch for smooth UI during large file loads
- **Config Persistence**: Stores last directory and file path

#### Architecture
- `python/main.py` - Application entry point
- `python/main_window.py` - Main UI window (622 lines)
- `python/log_parser.py` - Async parser with batching (305 lines)
- `python/log_table_model.py` - Qt Model/View (230 lines)
- `python/log_entry.py` - Data models (197 lines)
- `python/config.py` - Configuration (135 lines)

#### Documentation
- README.md - Updated with Python v1.0 focus
- USER_GUIDE.md - Comprehensive usage guide
- RELEASE_v1.0.md - Detailed release notes
- CHANGELOG.md - This file

#### Testing
- `test_integration.py` - Full application integration test
- `test_filter_search.py` - Filter/search performance tests
- `test_parser.py` - Parser unit tests
- Test coverage for all major features

### Changed

- **Main Version**: Python GUI is now the primary/recommended version
- **C++ Version**: Marked as deprecated/legacy (still available for reference)
- **Config Format**: Two-line format (directory + file) with backward compatibility

### Deprecated

- **C++ Terminal Version**: No longer actively maintained, use Python GUI version

