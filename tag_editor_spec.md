# Tag Editor Specification - LogReader v1.1

## Overview

This specification defines the Tag Editor feature for LogReader v1.1, which allows users to customize log level tags (names and colors) for different log systems.

---

## Background

**Current Limitation**: LogReader v1.0 has hardcoded log levels with fixed colors:
- DEBUG (Cyan)
- INFO (Green)
- WARN (Yellow)
- ERROR (Red)
- HEADER (Blue)
- FOOTER (Blue)

**Problem**: Different logging systems use different tag names and may have different severity levels. Users need to customize tags for their specific log formats.

**Examples**:
- Android logcat: VERBOSE, DEBUG, INFO, WARN, ERROR, FATAL
- syslog: EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, DEBUG
- Custom systems: TRACE, DEBUG, INFO, NOTICE, WARN, ERROR, CRITICAL, FATAL

---

## Requirements

### Change A: Tag Editor Dialog

**Current**: Help → Tag Colors (read-only display)

**New**: Help → Tag Editor (editable dialog)

**Features**:
1. **List of Tags**: Display all current log level tags
2. **Add Tag**: Button to add a new tag
3. **Remove Tag**: Button to remove selected tag (with confirmation)
4. **Edit Tag**: Double-click or Edit button to modify tag
5. **Color Picker**: Visual color selector for each tag
6. **Preview**: Show tag with current color
7. **Reset to Defaults**: Button to restore default tags

**UI Layout**:
```
┌─────────────────────────────────────────────┐
│ Tag Editor                          [X]     │
├─────────────────────────────────────────────┤
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Tag Name    │ Color   │ Preview         │ │
│ ├─────────────┼─────────┼─────────────────┤ │
│ │ DEBUG       │ [Cyan]  │ DEBUG           │ │
│ │ INFO        │ [Green] │ INFO            │ │
│ │ WARN        │ [Yellow]│ WARN            │ │
│ │ ERROR       │ [Red]   │ ERROR           │ │
│ │ HEADER      │ [Blue]  │ HEADER          │ │
│ │ FOOTER      │ [Blue]  │ FOOTER          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [Add Tag] [Edit Tag] [Remove Tag]           │
│                                             │
│ [Reset to Defaults]    [OK] [Cancel]        │
└─────────────────────────────────────────────┘
```

**Add/Edit Tag Dialog**:
```
┌─────────────────────────────────────┐
│ Add/Edit Tag               [X]      │
├─────────────────────────────────────┤
│                                     │
│ Tag Name:  [_______________]        │
│                                     │
│ Color:     [████████] [Choose...]   │
│                                     │
│ Preview:   [TAG NAME IN COLOR]      │
│                                     │
│            [OK] [Cancel]            │
└─────────────────────────────────────┘
```

### Change B: Tag Parsing Order

**Assumption**: Tags are parsed in the order they appear in the log file format.

**Current Format**:
```
timestamp<FS>LEVEL<FS>message<FS>source
```

**Parser Behavior**:
1. Parse the LEVEL field (position 1 after split)
2. Match against known tags (case-insensitive)
3. If tag is unknown:
   - **Option 1**: Create new tag with default color (gray)
   - **Option 2**: Treat as INFO level
   - **Option 3**: Show as "UNKNOWN" with gray color

**Recommendation**: Option 1 (auto-create with default color)
- User-friendly for new log formats
- Allows discovery of tags
- User can customize color later in Tag Editor

### Change C: Save Tags to Configuration

**Current Config Format** (logreader_config.txt):
```
/path/to/last/directory
/path/to/last/file.log
```

**New Config Format** (see Change D for JSON migration):
```
/path/to/last/directory
/path/to/last/file.log
TAGS:DEBUG:cyan,INFO:green,WARN:yellow,ERROR:red
```

**Problems with Current Format**:
- Not extensible
- Hard to parse complex data
- No structure for nested data
- No type information

**Better**: Migrate to JSON (see Change D)

### Change D: Migrate to JSON Configuration

**Recommendation**: YES, migrate to JSON

**Reasons**:
1. **Extensibility**: Easy to add new configuration options
2. **Structure**: Nested data, lists, objects
3. **Readability**: Human-readable and editable
4. **Standard**: Python's `json` module is built-in
5. **Future-Proof**: Supports complex preferences (themes, layouts, recent files, etc.)

**New Config File**: `logreader_config.json`

**Format**:
```json
{
  "version": "1.1",
  "last_directory": "/path/to/last/directory",
  "last_file": "/path/to/last/file.log",
  "tags": [
    {
      "name": "DEBUG",
      "color": "#00FFFF",
      "enabled": true
    },
    {
      "name": "INFO",
      "color": "#00FF00",
      "enabled": true
    },
    {
      "name": "WARN",
      "color": "#FFFF00",
      "enabled": true
    },
    {
      "name": "ERROR",
      "color": "#FF0000",
      "enabled": true
    },
    {
      "name": "HEADER",
      "color": "#0000FF",
      "enabled": true
    },
    {
      "name": "FOOTER",
      "color": "#0000FF",
      "enabled": true
    }
  ],
  "window": {
    "width": 1200,
    "height": 800,
    "maximized": false
  },
  "preferences": {
    "font_size": 9,
    "font_family": "Consolas",
    "theme": "light"
  }
}
```

**Migration Strategy**:
1. On startup, check if `logreader_config.json` exists
2. If not, check if old `logreader_config.txt` exists
3. If old config exists:
   - Parse old format
   - Convert to JSON format
   - Save as `logreader_config.json`
   - Keep old file (don't delete, for safety)
4. If neither exists, create default JSON config

**Backward Compatibility**:
- Read old `.txt` format ✓
- Auto-migrate to `.json` ✓
- Don't break existing users ✓

---

## Data Model

### Tag Data Structure

**Python**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class LogTag:
    """Represents a log level tag with customizable color."""
    name: str              # Tag name (e.g., "DEBUG", "INFO")
    color: str             # Hex color (e.g., "#00FFFF")
    enabled: bool = True   # Whether tag appears in filters
    order: int = 0         # Display order in UI

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "color": self.color,
            "enabled": self.enabled,
            "order": self.order
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LogTag':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            name=data["name"],
            color=data["color"],
            enabled=data.get("enabled", True),
            order=data.get("order", 0)
        )
```

### Configuration Data Structure

**Python**:
```python
@dataclass
class AppConfig:
    """Application configuration."""
    version: str = "1.1"
    last_directory: str = ""
    last_file: str = ""
    tags: List[LogTag] = None
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    font_size: int = 9
    font_family: str = "Consolas"
    theme: str = "light"

    def __post_init__(self):
        if self.tags is None:
            self.tags = self._default_tags()

    @staticmethod
    def _default_tags() -> List[LogTag]:
        """Return default log tags."""
        return [
            LogTag("DEBUG", "#00FFFF", True, 0),
            LogTag("INFO", "#00FF00", True, 1),
            LogTag("WARN", "#FFFF00", True, 2),
            LogTag("ERROR", "#FF0000", True, 3),
            LogTag("HEADER", "#0000FF", True, 4),
            LogTag("FOOTER", "#0000FF", True, 5),
        ]

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "version": self.version,
            "last_directory": self.last_directory,
            "last_file": self.last_file,
            "tags": [tag.to_dict() for tag in self.tags],
            "window": {
                "width": self.window_width,
                "height": self.window_height,
                "maximized": self.window_maximized
            },
            "preferences": {
                "font_size": self.font_size,
                "font_family": self.font_family,
                "theme": self.theme
            }
        }
```

---

## Implementation Plan

### Phase 1: Config Migration (Foundation)

**Files to Modify**:
- `python/config.py` - ConfigManager class

**Tasks**:
1. Create `AppConfig` and `LogTag` dataclasses
2. Add JSON load/save methods to ConfigManager
3. Add migration logic (txt → json)
4. Update `load_last_directory()` and `load_last_file_path()` to use JSON
5. Add `load_tags()` and `save_tags()` methods
6. Test migration with existing config files

**Acceptance Criteria**:
- ✓ Old `.txt` config auto-migrates to `.json`
- ✓ Default config created if none exists
- ✓ Tags loaded correctly from JSON
- ✓ Backward compatible with v1.0 configs

### Phase 2: Tag Data Model Integration

**Files to Modify**:
- `python/log_entry.py` - Update LogLevel to use dynamic tags
- `python/log_table_model.py` - Use dynamic tag colors
- `python/log_parser.py` - Parse unknown tags gracefully

**Tasks**:
1. Replace hardcoded LogLevel enum with dynamic tag lookup
2. Update color mapping to use tag colors from config
3. Handle unknown tags (create with default color)
4. Update parser to be tag-agnostic

**Acceptance Criteria**:
- ✓ Dynamic tags work in parsing
- ✓ Dynamic colors display correctly
- ✓ Unknown tags handled gracefully

### Phase 3: Tag Editor UI

**Files to Create**:
- `python/tag_editor_dialog.py` - Tag Editor dialog

**Files to Modify**:
- `python/main_window.py` - Add Tag Editor menu item

**Tasks**:
1. Create `TagEditorDialog` class (QDialog)
2. Add tag list widget (QTableWidget)
3. Add Add/Edit/Remove buttons
4. Add color picker (QColorDialog)
5. Add Reset to Defaults button
6. Implement save/cancel logic
7. Update main window to open dialog

**UI Components**:
- QTableWidget for tag list (name, color, preview)
- QPushButton for actions (Add, Edit, Remove, Reset)
- QColorDialog for color selection
- Custom delegate for color preview column

**Acceptance Criteria**:
- ✓ Can add new tags
- ✓ Can edit existing tags
- ✓ Can remove tags (with confirmation)
- ✓ Can change tag colors
- ✓ Can reset to defaults
- ✓ Changes persist to config file

### Phase 4: Filter Integration (CRITICAL)

**IMPORTANT**: Filter checkboxes MUST be dynamically generated based on tag names from config, not hardcoded.

**Files to Modify**:
- `python/main_window.py` - Update filter checkboxes to use dynamic tags

**Current Problem**:
- Filters are hardcoded: `self.debug_filter`, `self.info_filter`, `self.warn_filter`, etc.
- Filter names are fixed in code

**New Approach**:
- Generate filter checkboxes dynamically from `config.tags`
- Use dictionary: `self.tag_filters = {tag.name: QCheckBox(tag.name) for tag in tags}`
- Rebuild filters when tags change in Tag Editor
- Filter colors match tag colors from config

**Tasks**:
1. Replace hardcoded filter checkboxes with dynamic generation
2. Update `_apply_filters()` to iterate through `self.tag_filters`
3. Handle tag additions/removals (refresh filter UI)
4. Persist filter state across tag changes (save enabled state to config)
5. Update filter layout to accommodate variable number of tags

**Acceptance Criteria**:
- ✓ Filter checkboxes dynamically generated from config.tags
- ✓ Adding/removing tags in Tag Editor immediately updates filter UI
- ✓ Filter colors match tag colors
- ✓ Filter state persists across app restarts
- ✓ Works with any number of tags (not just 6 hardcoded ones)

---

## Edge Cases & Error Handling

### Unknown Tags in Log File

**Scenario**: Log file contains tag not in config (e.g., "VERBOSE")

**Behavior**:
1. Parser encounters unknown tag
2. Create new LogTag("VERBOSE", "#808080", True, 999)
3. Add to config automatically
4. Display in gray until user customizes
5. Notify user: "New tag discovered: VERBOSE (click to customize)"

### Tag Name Conflicts

**Scenario**: User tries to add tag with duplicate name

**Behavior**:
1. Validate tag name before adding
2. Show error: "Tag 'DEBUG' already exists"
3. Don't allow duplicate names (case-insensitive)

### Color Format Validation

**Scenario**: Invalid color format in config file

**Behavior**:
1. Try to parse hex color (#RRGGBB)
2. If invalid, fall back to gray (#808080)
3. Log warning: "Invalid color for tag 'DEBUG', using default"

### Config File Corruption

**Scenario**: JSON config file is corrupted

**Behavior**:
1. Try to load JSON
2. If parse error, log warning
3. Fall back to default config
4. Keep corrupted file as `.bak` for recovery
5. Notify user: "Config file corrupted, restored defaults"

### Migration Failure

**Scenario**: Old config file exists but can't be read

**Behavior**:
1. Try to read old format
2. If error, log warning
3. Create fresh default config
4. Keep old file untouched

---

## Configuration File Specification

### File Location

**Default**: `logreader_config.json` in current working directory

**Future**: Consider platform-specific locations:
- Windows: `%APPDATA%/LogReader/config.json`
- macOS: `~/Library/Application Support/LogReader/config.json`
- Linux: `~/.config/logreader/config.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "description": "Config format version"
    },
    "last_directory": {
      "type": "string",
      "description": "Last opened directory"
    },
    "last_file": {
      "type": "string",
      "description": "Last opened file path"
    },
    "tags": {
      "type": "array",
      "description": "Log level tags",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
          "enabled": {"type": "boolean"},
          "order": {"type": "integer"}
        },
        "required": ["name", "color"]
      }
    },
    "window": {
      "type": "object",
      "properties": {
        "width": {"type": "integer"},
        "height": {"type": "integer"},
        "maximized": {"type": "boolean"}
      }
    },
    "preferences": {
      "type": "object",
      "properties": {
        "font_size": {"type": "integer"},
        "font_family": {"type": "string"},
        "theme": {"type": "string"}
      }
    }
  },
  "required": ["version"]
}
```

---

## Testing Plan

### Unit Tests

1. **Config Migration**:
   - Old format → JSON conversion
   - Default config creation
   - JSON load/save

2. **Tag Operations**:
   - Add tag
   - Remove tag
   - Edit tag
   - Duplicate name detection

3. **Unknown Tag Handling**:
   - Auto-create unknown tags
   - Default color assignment

### Integration Tests

1. **Tag Editor Dialog**:
   - Open/close dialog
   - Add/edit/remove tags
   - Color picker
   - Save/cancel

2. **Filter Updates**:
   - Checkboxes reflect current tags
   - Add tag → new checkbox
   - Remove tag → checkbox removed

3. **Config Persistence**:
   - Changes save to JSON
   - Changes persist across restarts

### User Acceptance Tests

1. Customize tag colors for Android logcat
2. Add custom tags for internal logging system
3. Remove unused tags
4. Reset to defaults after customization

---

## Future Enhancements (v1.2+)

### Tag Presets

Allow users to save/load tag sets for different log systems:
- Android logcat preset
- syslog preset
- Custom presets

### Tag Icons

Allow custom icons for tags (in addition to colors)

### Tag Grouping

Group related tags (e.g., all error-level tags)

### Tag Aliases

Allow multiple names to map to same tag (e.g., "ERR" → "ERROR")

### Tag Filtering Rules

Advanced filtering: "Show ERROR and above" (severity-based)

---

## Migration Guide for Users

### Automatic Migration

When you upgrade to v1.1:
1. Your existing config will auto-migrate to JSON
2. Old config file will remain unchanged
3. Default tags will match v1.0 behavior
4. No action required

### Customizing Tags

1. Help → Tag Editor
2. Select tag to edit
3. Choose new color
4. Click OK to save

### Adding Tags for New Log Formats

1. Open log file with new tags
2. New tags appear automatically in gray
3. Customize colors via Tag Editor

---

## Open Questions

1. **Tag Ordering**: Should users be able to reorder tags in the editor?
   - **Recommendation**: Yes, add up/down buttons

2. **Tag Import/Export**: Should users be able to share tag configs?
   - **Recommendation**: v1.2 feature - export tags as JSON snippet

3. **Tag Validation**: What characters are allowed in tag names?
   - **Recommendation**: Alphanumeric + underscore, no spaces

4. **Maximum Tags**: Should there be a limit on number of tags?
   - **Recommendation**: No hard limit, but warn if > 20 tags

5. **Default Color**: What color for auto-created unknown tags?
   - **Recommendation**: Gray (#808080)

---

## Summary

This specification defines a flexible tag system for LogReader v1.1 that:
- ✅ Allows customization of tag names and colors
- ✅ Migrates config to JSON for extensibility
- ✅ Handles unknown tags gracefully
- ✅ Maintains backward compatibility with v1.0
- ✅ Provides intuitive UI for tag management

**Estimated Effort**: 3-5 days of development + testing

**Target Release**: LogReader v1.1 (Q2 2025)
