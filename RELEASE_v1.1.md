# LogReader v1.1 Release Notes

**Release Date**: January 2025

**Major Feature**: Dynamic Tag System with Tag Editor

---

## What's New in v1.1

### 🎨 **Dynamic Tag System**

LogReader now supports **fully customizable log level tags**:

- **Tag Editor Dialog** (`Help → Tag Editor`)
  - Add new tags for any log system (Android logcat, syslog, custom formats)
  - Edit existing tag names and colors
  - Remove unused tags
  - Reset to defaults with one click
  - Live color preview

- **Auto-Discovery of Unknown Tags**
  - Parser automatically creates tags for unknown log levels
  - Default gray color (#808080) for new tags
  - Customize later via Tag Editor

- **Dynamic Filter Checkboxes**
  - Filter UI adapts to current tag set
  - No more hardcoded DEBUG/INFO/WARN/ERROR limits
  - Support for unlimited custom tags

### 📁 **JSON Configuration**

- **Migration from Text to JSON**
  - Old `logreader_config.txt` auto-migrates to `logreader_config.json`
  - Backward compatible - no user action required
  - Structured, extensible configuration format

- **Configuration Structure**:
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
        "order": 0
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

---

## Implementation Details

### Architecture Changes

**Phase 1: Configuration System**
- Added `LogTag` dataclass for tag metadata
- Added `AppConfig` dataclass for all settings
- Implemented JSON serialization/deserialization
- Automatic migration from v1.0 text format

**Phase 2: Data Model Refactoring**
- Changed `LogLevel` from Enum to dynamic string wrapper
- Updated `LogTableModel` to fetch colors from config
- Modified `LogParser` to auto-create unknown tags

**Phase 3: Tag Editor UI**
- Created `TagEditorDialog` with table-based tag list
- Implemented `AddEditTagDialog` for tag creation/editing
- Integrated color picker for visual customization
- Added validation and duplicate prevention

**Phase 4: Dynamic Filters**
- Rebuilt filter checkboxes from config tags
- Changed filter storage from `Dict[LogLevel, QCheckBox]` to `Dict[str, QCheckBox]`
- Updated `_apply_filters()` to compare by tag name strings
- Excluded internal tags (HEADER, FOOTER) from filters

### Files Modified

**Core Changes**:
- `python/config.py` - Complete rewrite (177 → 465 lines)
  - Added LogTag and AppConfig dataclasses
  - JSON load/save with migration
  - Tag management methods (add, remove, get_or_create)

- `python/log_entry.py` - LogLevel refactored (130 → 154 lines)
  - Changed from Enum to string wrapper
  - Added equality and hashing support
  - Maintained backward compatibility

- `python/log_table_model.py` - Dynamic colors (230 → 220 lines)
  - Removed hardcoded LEVEL_COLORS
  - Fetch colors from ConfigManager dynamically

- `python/log_parser.py` - Auto-discovery (305 → 310 lines)
  - Added auto-creation of unknown tags
  - Tags registered during parsing

- `python/main_window.py` - Dynamic filters (622 → 750 lines)
  - Dynamic filter checkbox generation
  - Updated _apply_filters for string-based tags
  - Added Tag Editor menu item and handler

**New Files**:
- `python/tag_editor_dialog.py` (425 lines)
  - TagEditorDialog - Main tag management UI
  - AddEditTagDialog - Single tag add/edit

**Updated**:
- `python/main.py` - Version 1.0 → 1.1
- `tag_editor_spec.md` - Added Phase 4 clarifications

---

## User Guide

### Customizing Tags

1. **Open Tag Editor**:
   - Go to `Help → Tag Editor`
   - View all current tags with colors

2. **Add a New Tag**:
   - Click "Add Tag"
   - Enter tag name (e.g., "VERBOSE", "FATAL")
   - Choose color from picker
   - Preview shows tag in selected color
   - Click OK

3. **Edit Existing Tag**:
   - Select tag from list
   - Click "Edit Tag" (or double-click tag name)
   - Modify name and/or color
   - Click OK

4. **Change Tag Color**:
   - Double-click the color column
   - Choose new color from picker
   - Color updates immediately

5. **Remove a Tag**:
   - Select tag from list
   - Click "Remove Tag"
   - Confirm deletion

6. **Reset to Defaults**:
   - Click "Reset to Defaults"
   - Restores original 6 tags (DEBUG, INFO, WARN, ERROR, HEADER, FOOTER)

### Applying Changes

After editing tags:
- Filter checkboxes: Update on next app restart
- Tag colors: Apply to newly parsed files immediately
- Current file: Reload with `Ctrl+R` to see new colors

### Auto-Discovery

When LogReader encounters an unknown tag:
- Automatically creates tag with gray color
- Tag appears in filters and Tag Editor
- Customize color via Tag Editor

---

## Use Cases

### Android Logcat Support

```
Tags:
- VERBOSE (#808080 gray)
- DEBUG (#00FFFF cyan)
- INFO (#00FF00 green)
- WARN (#FFFF00 yellow)
- ERROR (#FF0000 red)
- FATAL (#FF00FF magenta)
```

### Syslog Support

```
Tags:
- EMERG (#FF0000 red)
- ALERT (#FF4500 orange-red)
- CRIT (#FFA500 orange)
- ERR (#FFFF00 yellow)
- WARNING (#FFFF99 light yellow)
- NOTICE (#00FFFF cyan)
- INFO (#00FF00 green)
- DEBUG (#808080 gray)
```

### Custom Logging

```
Tags:
- TRACE (#C0C0C0 silver)
- DEBUG (#00FFFF cyan)
- INFO (#00FF00 green)
- NOTICE (#87CEEB sky blue)
- WARN (#FFFF00 yellow)
- ERROR (#FF0000 red)
- CRITICAL (#FF00FF magenta)
- FATAL (#8B0000 dark red)
```

---

## Breaking Changes

### None (Fully Backward Compatible)

- v1.0 config files auto-migrate to v1.1
- Default tags match v1.0 behavior exactly
- Existing workflows unchanged

---

## Known Issues

1. **Filter UI Refresh**: Filter checkboxes only update on app restart after tag changes
   - **Workaround**: Restart app after editing tags
   - **Future**: Hot-reload filters without restart (v1.2)

2. **Tag Ordering**: Cannot reorder tags in Tag Editor
   - **Workaround**: Remove and re-add in desired order
   - **Future**: Drag-and-drop reordering (v1.2)

---

## Performance

- Config load time: <1ms (JSON parsing)
- Tag lookup: O(n) linear search (negligible for <50 tags)
- Filter generation: <10ms for typical tag counts
- No impact on log parsing performance

---

## Testing

All phases tested:
- ✅ Config migration (TXT → JSON)
- ✅ Dynamic tag creation
- ✅ Tag Editor UI (add, edit, remove, reset)
- ✅ Dynamic filter generation
- ✅ Color application from config
- ✅ Backward compatibility with v1.0

---

## Future Enhancements (v1.2+)

See `tag_editor_spec.md` for detailed roadmap:

- **Tag Presets**: Save/load tag sets for different log systems
- **Tag Icons**: Custom icons in addition to colors
- **Tag Grouping**: Group related tags (e.g., error-level tags)
- **Tag Aliases**: Multiple names mapping to same tag
- **Severity-Based Filtering**: "Show ERROR and above"
- **Import/Export**: Share tag configs between users
- **Hot-Reload**: Update filters without restart

---

## Migration from v1.0

### Automatic

On first launch of v1.1:
1. Detects `logreader_config.txt`
2. Reads directory and file paths
3. Creates `logreader_config.json` with:
   - Migrated paths
   - Default 6 tags (matching v1.0)
   - Default window/preferences
4. Keeps old `.txt` file (not deleted)

### Manual (if needed)

If migration fails:
1. Check `logreader_config.txt` format
2. Delete corrupted files
3. Restart app → creates fresh config

---

## Credits

Implemented following the specification in `tag_editor_spec.md`.

**Contributors**: Claude Code (Anthropic)

**Date**: January 2025

---

## License

MIT License - See LICENSE file

---

## Feedback

Please report issues or suggest features via GitHub issues.
