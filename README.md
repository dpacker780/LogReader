# LogReader v1.2


![LogReader UI Screenshot](https://github.com/dpacker780/LogReader/blob/master/logreader_UI.png)

**A modern, professional GUI log viewer built with Python and PyQt6.**

LogReader is a cross-platform log file viewer with dynamic tag system, real-time filtering, search, and navigation capabilities. LogReader was created to address a specific challenge I ran into when working with AI tools, especially with a complex code-base that outputs a lot of log information during development.  Asking AI to parse through logs often leads to errors or misinterpretation, especially with temporal information, which led to bad assumptions, incorrect code-changes, chasing red-herrings. Since I code mainly in C++ and my logs for a running  app can generate 1000s of log entries I needed a simpler way. To address it I built this simple tool (using Anthropic's Claude), to quickly find relevant log entries from my log generator and be able to copy-paste them into the conversation.  It's useful beyond that obviously, anytime you want to read through large dev log files to understand what might be occuring.

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

### v1.2 New Features
- **📊 Tag Count Display**: Optional entry counts next to filter checkboxes
  - Per-tag "Show Count" toggle in Tag Editor (e.g., `WARN [42]`, `ERROR [5]`)
  - Default: WARN and ERROR show counts, others don't
  - Counts update dynamically with search/filters
  - Light green count text for readability

- **📂 File Filtering**: Filter logs by source file
  - Dropdown between Search and Jump to Line
  - Auto-populated with files from current log
  - Alphabetically sorted with "All" option
  - Combines with level filters and search

- **🔍 Message Detail View**: View long messages easily
  - Hover tooltips (120-char width) for quick viewing
  - Ctrl+M for detail dialog with copy functionality
  - Perfect for very long log messages

- **📁 Recent Files**: Quick access to recently opened files
  - File → Recent Files menu (last 10 files)
  - Auto-loads last file on startup
  - Checkmark on currently open file
  - "Clear Recent Files" option

- **🔔 File Change Notification**: Know when log file updates
  - Red status bar notification when file changes
  - Manual reload with Ctrl+R
  - Monitors current file with QFileSystemWatcher

- **🗂️ Separate Source Columns**: Better organization
  - File, Function, Line as separate columns
  - Easier to scan and filter
  - New 6-field log format support

### v1.1 Features
- **🎨 Dynamic Tag System**: Fully customizable log level tags with Tag Editor
- **🔍 Context Navigation**: Double-click to clear filters and see surrounding context
- **⚡ Dynamic Filtering**: Unlimited custom tags with OR logic
- **📁 JSON Configuration**: Structured config with auto-migration

### Search and Filter
- **Real-time Filtering**: Filter by log levels and source files without re-parsing
- **File Filtering**: Dropdown to show only entries from specific source files
- **Instant Search**: Search through log messages with live results
- **Combined Logic**: Level filters use OR logic, file filter and search use AND logic
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
| **Show message details** | Ctrl+M |
| **Select all visible** | Ctrl+A |
| **Clear search** | Esc |
| **Jump to line** | Enter (in Jump field) |
| **Quit application** | Ctrl+Q |
| **Show context** | Double-click entry |
| **View long messages** | Hover over Message column |

#### Status Bar Information

The status bar at the bottom shows (with visual separators):
- **Status**: Current operation (Ready, Parsing, Complete, etc.)
- **File**: Current file name
- **Entries**: Total count (and visible count when filtered)
- **Line Info**: Reserved for future features

### Log Format

The parser expects log entries using ASCII field separators (character 31):

**v1.2+ Format (6 fields - separate file, function, line):**
```
timestamp<FS>LEVEL<FS>message<FS>source_file<FS>function<FS>line_number
```

Where `<FS>` represents the ASCII field separator (char 31, 0x1F).

**Example:**
```
16:29:40.318<FS>DEBUG<FS>Vulkan loader version: 1.4.304<FS>Vulkan.cpp<FS>initVulkan<FS>92
16:29:40.587<FS>INFO<FS>Supported instance extensions:<FS>Vulkan.cpp<FS>initVulkan<FS>106
16:29:40.629<FS>ERROR<FS>Failed to create surface<FS>Vulkan.cpp<FS>createSurface<FS>156
```

The 6-field format enables file filtering and separate column display.

### Architecture

- **python/main.py** - Application entry point (v1.2)
- **python/main_window.py** - Main UI window (PyQt6, 1000+ lines)
- **python/log_parser.py** - Async log file parser with 6-field format support
- **python/log_table_model.py** - Qt Model/View with separate File/Function/Line columns
- **python/log_entry.py** - Data models (LogEntry, LogLevel)
- **python/config.py** - JSON configuration with tag management and recent files (v1.2)
- **python/tag_editor_dialog.py** - Tag Editor UI with Show Count toggle (v1.2)
- **python/message_detail_dialog.py** - Message detail viewer (v1.2)

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
  "version": "1.2",
  "last_directory": "/path/to/logs",
  "last_file": "/path/to/file.log",
  "recent_files": ["/path/to/file1.log", "/path/to/file2.log"],
  "max_recent_files": 10,
  "tags": [
    {
      "name": "DEBUG",
      "color": "#00FFFF",
      "enabled": true,
      "order": 0,
      "message_color": "#FFFFFF",
      "message_match_tag": false,
      "show_count": false
    },
    {
      "name": "WARN",
      "color": "#FFFF00",
      "enabled": true,
      "order": 2,
      "message_color": "#FFFFFF",
      "message_match_tag": false,
      "show_count": true
    }
  ],
  "window": { "width": 1200, "height": 800, "maximized": false },
  "preferences": { "font_size": 9, "font_family": "Consolas", "theme": "light" }
}
```

---

## Roadmap

### Future Enhancements (v1.3+)

- Function name filtering (dropdown like file filter)
- Tag Icons (in addition to colors)
- Bookmarks for important lines (Navigate (N)ext / (P)revious)
- Export filtered results
- Custom column ordering and widths
- Configurable log format (user-defined field mappings)
- Log level statistics panel
- Dark theme support

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Version History

### v1.2 (File Filtering & Enhancements) - January 2025
- **File Filtering**: Dropdown to filter logs by source file
- **Separate Source Columns**: File, Function, Line as individual columns
- **Tag Counts**: Optional entry counts next to filter checkboxes
- **Message Detail View**: Hover tooltips and Ctrl+M detail dialog
- **Recent Files**: Auto-load last file, File → Recent Files menu
- **File Change Notification**: Red status when file changes externally
- **6-Field Log Format**: Separate file, function, line fields
- **Enhanced Tag Editor**: Filter checkbox and Show Count toggle
- **Performance**: Tag count updates, file filter caching

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

- **[RELEASE_v1.2.md](RELEASE_v1.2.md)** - Detailed v1.2 release notes
- **[RELEASE_v1.1.md](RELEASE_v1.1.md)** - Detailed v1.1 release notes
- **[RELEASE_v1.0.md](RELEASE_v1.0.md)** - v1.0 release notes

---

**Ready to get started?** See [GETTING_STARTED.md](GETTING_STARTED.md) for a 5-minute setup guide!
