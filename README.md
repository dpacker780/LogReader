# LogReader v1.1


![LogReader UI Screenshot](https://github.com/dpacker780/LogReader/blob/master/logreader_UI.png)

**A modern, professional GUI log viewer built with Python and PyQt6.**

Cross-platform log file viewer with dynamic tag system, real-time filtering, search, and navigation capabilities.

> **Note**: This is a Python rewrite of the original C++ terminal version. The C++ version is available in a separate repository for terminal-only environments.

---

## Features

### Core Features
- **Native File Dialog**: Standard file picker with last directory memory
- **Professional Status Bar**: Real-time status, file info, entry counts with clean separators
- **Line Numbers**: Reference specific log entries easily with original file line numbers
- **Jump to Line**: Navigate directly to any line number with auto-filter clearing
- **Fast Log Parsing**: Async parsing with progress updates (handles 100k+ entries smoothly)
- **Row Selection**: Select single or multiple rows with Ctrl+C to copy
- **Keyboard Shortcuts**: Efficient workflow with Ctrl+O, Ctrl+R, Ctrl+C, Esc, Ctrl+Q

### v1.1 New Features
- **🎨 Dynamic Tag System**: Fully customizable log level tags
  - Tag Editor (`Help → Tag Editor`) for complete tag management
  - Add, edit, remove, and reset tags
  - Customize tag colors and message colors
  - "Match Tag Color" option for messages to stand out
  - Auto-discovery of unknown tags with default gray color

- **🔍 Context Navigation**: Double-click any filtered entry to clear filters and see surrounding context

- **⚡ Dynamic Filtering**: Filter checkboxes adapt to your tag configuration
  - Supports unlimited custom tags
  - No more hardcoded DEBUG/INFO/WARN/ERROR limits
  - OR logic: Check multiple tags to show all matching entries

- **📁 JSON Configuration**: Structured, extensible config format
  - Auto-migration from v1.0 text format
  - Stores tags, window settings, and preferences
  - Backward compatible

### Search and Filter
- **Real-time Filtering**: Filter by any log levels without re-parsing
- **Instant Search**: Search through log messages with live results
- **Combined Logic**: Filters use OR logic, search uses AND logic with filters
- **Quick Clear**: Esc to clear search, double-click to clear all filters

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
- **Context View**: Double-click any entry to clear filters and see surrounding context

#### Customizing Tags (v1.1)

1. **Open Tag Editor**: `Help → Tag Editor`
2. **Edit Tag Colors**: Double-click the "Tag Color" column
3. **Edit Message Colors**: Double-click the "Message Color" column
   - Check "Match Tag Color" to make messages stand out (e.g., red ERROR messages)
   - Uncheck to use custom message color (default: white)
4. **Add New Tags**: Click "Add Tag" button
5. **Remove Tags**: Select tag and click "Remove Tag"
6. **Reset**: Click "Reset to Defaults" to restore original 6 tags

#### Filtering and Search

- **Level Filters**: Check boxes to show only specific log levels (OR logic, no boxes = show all)
- **Search**: Type in search box to filter by message content (AND logic with level filters)
- **Clear Filters**: Esc in search box, or double-click any entry to clear all and see context
- **Auto-Discovery**: Unknown tags appear automatically with gray color, customize via Tag Editor

#### Shortcuts

| Action | Shortcut |
|--------|----------|
| **Open file dialog** | Ctrl+O |
| **Reload current file** | Ctrl+R |
| **Copy selected rows** | Ctrl+C |
| **Select all visible** | Ctrl+A |
| **Clear search** | Esc |
| **Jump to line** | Enter (in Jump field) |
| **Quit application** | Ctrl+Q |
| **Show context** | Double-click entry |

#### Status Bar Information

The status bar at the bottom shows (with visual separators):
- **Status**: Current operation (Ready, Parsing, Complete, etc.)
- **File**: Current file name
- **Entries**: Total count (and visible count when filtered)
- **Line Info**: Reserved for future features

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

- **python/main.py** - Application entry point (v1.1)
- **python/main_window.py** - Main UI window (PyQt6, 800+ lines)
- **python/log_parser.py** - Async log file parser with batching
- **python/log_table_model.py** - Qt Model/View for efficient display
- **python/log_entry.py** - Data models (LogEntry, LogLevel)
- **python/config.py** - JSON configuration with tag management (v1.1)
- **python/tag_editor_dialog.py** - Tag Editor UI (v1.1)

### Performance

- **Parsing**: ~4,400 entries/sec on typical hardware
- **Filtering**: <1ms for 1,000+ entries
- **Async Design**: UI remains responsive during large file loads
- **Memory Efficient**: Uses filtered indices instead of copying entries
- **Config Load**: <1ms (JSON parsing)

---

## Use Cases

### Different Log Systems

LogReader v1.1 supports any log format via customizable tags:

**Android Logcat**:
```
Custom tags: VERBOSE, DEBUG, INFO, WARN, ERROR, FATAL
Set ERROR to red with "Match Tag Color" for visibility
```

**syslog**:
```
Custom tags: EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, DEBUG
```

**Custom Systems**:
```
Add any tags your system uses (TRACE, NOTICE, CRITICAL, etc.)
Auto-discovered unknown tags appear in gray
```

### Workflow Examples

**Finding Specific Errors**:
1. Check ERROR filter box
2. Search for "timeout"
3. Find the relevant entry
4. **Double-click** to clear filters and see what led to the error

**Debugging Sequences**:
1. Search for "connection opened"
2. Browse results
3. **Double-click** interesting entry to see full connection lifecycle

**Custom Highlighting**:
1. Open Tag Editor
2. Set ERROR message color to "Match Tag Color"
3. ERROR messages now stand out in red!

---

## Configuration

### Config File Location

- **v1.1**: `logreader_config.json` (JSON format)
- **v1.0**: `logreader_config.txt` (auto-migrates to JSON)

### Config Contents

```json
{
  "version": "1.1",
  "last_directory": "/path/to/logs",
  "last_file": "/path/to/file.log",
  "tags": [
    {
      "name": "DEBUG",
      "color": "#00FFFF",
      "enabled": true,
      "order": 0,
      "message_color": "#FFFFFF",
      "message_match_tag": false
    }
  ],
  "window": { "width": 1200, "height": 800 },
  "preferences": { "font_size": 9, "theme": "light" }
}
```

---

## Roadmap

### Future Enhancements (v1.2+)

- Recent files list (File → Recent)
- Tag Icons (in addition to colors)
- Bookmarks for important lines (Navigate (N)ext / (P)revious))
- Export filtered results
- Custom column ordering
- Live tail mode (watch file for changes) and notifier
- Log level statistics

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Version History

### v1.1 (Dynamic Tags) - January 2025
- **Dynamic Tag System**: Fully customizable log level tags
- **Tag Editor**: Add, edit, remove, customize colors
- **Message Colors**: Separate colors for tags and messages
- **Context Navigation**: Double-click to clear filters and see context
- **JSON Config**: Structured configuration with auto-migration
- **Dynamic Filters**: Unlimited custom tags
- **Auto-Discovery**: Unknown tags appear automatically
- **Polish**: Improved status bar with separators and margins

### v1.0 (Python GUI) - January 2025
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

---

## Documentation

- **[RELEASE_v1.1.md](RELEASE_v1.1.md)** - Detailed v1.1 release notes
- **[RELEASE_v1.0.md](RELEASE_v1.0.md)** - v1.0 release notes

---

**Ready to get started?** See [GETTING_STARTED.md](GETTING_STARTED.md) for a 5-minute setup guide!
