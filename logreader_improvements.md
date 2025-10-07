# LogReader Python - UI Improvements Specification

## Overview

This document specifies improvements to the Python/PyQt6 version of LogReader to create a more modern, GUI-native interface that moves away from the terminal UI constraints of the original C++ version.

## Current Status

The Python port has achieved feature parity with the C++ version:
- ✅ ASCII field separator parsing (char 31)
- ✅ Async parsing with progress updates
- ✅ Color-coded log levels
- ✅ Level filtering (checkboxes)
- ✅ Text search
- ✅ Row selection and Ctrl+C copy
- ✅ Menubar with File/Help menus
- ✅ Ctrl+R reload functionality
- ✅ Keyboard shortcuts (Ctrl+O, Ctrl+R, Ctrl+C, Esc, Ctrl+Q)

## Proposed UI Improvements

### Change A: File Dialog for Opening Files

**Current Behavior:**
- Top pane shows file path input field and "Open" button
- User must manually type or paste file path
- Legacy terminal-style interface

**Proposed Behavior:**
- Remove top pane entirely (file path input + Open button)
- Use native file dialog via `QFileDialog.getOpenFileName()`
- Triggered by:
  - File → Open... menu item (Ctrl+O)
  - Keyboard shortcut: Ctrl+O
- Remember last directory in config
- File type filter: "Log Files (*.log);;All Files (*.*)"

**Implementation Notes:**
- Update `ConfigManager` to save last directory (not just file path)
- `_on_open_clicked()` should invoke file dialog
- Dialog opens to last used directory
- Selected file automatically loads (no separate "Open" button needed)

**Benefits:**
- Standard GUI behavior users expect
- No manual path typing/errors
- Cleaner, less cluttered interface

---

### Change B: Status Bar

**Current Behavior:**
- File path shown in top pane input field
- Status message shown in top pane label
- Entry count shown above table: "Showing X of Y entries"
- Scattered information across UI

**Proposed Behavior:**
- Add proper `QStatusBar` at bottom of window
- Status bar sections (left to right):
  1. **Status message** (left): "Ready" / "Parsing..." / "Complete" / error messages
  2. **Active file** (center-left): "File: helix.log" or full path
  3. **Entry count** (center-right): "1,271 entries (326 visible)"
  4. **Line info** (right): "Line 42 of 1,271" (when table has focus)

**Implementation Notes:**
- Use `QMainWindow.statusBar()` to create status bar
- Use `addWidget()` and `addPermanentWidget()` for sections
- Update `_update_status()` method
- Update `_update_entry_count()` to write to status bar
- Remove status label from top pane
- Remove entry count label from table pane

**Format Examples:**
```
Ready | File: helix.log | 1,271 entries (326 visible) | Line 42 of 1,271
Parsing... 45% | File: test_input.log | 0 entries |
Complete: 1,271 entries from 1,369 lines | File: helix.log | 1,271 entries
Error: File not found | No file loaded | 0 entries
```

**Benefits:**
- Professional appearance
- Information always visible
- Doesn't take space from main content
- Standard GUI pattern

---

### Change C: Line Numbers Column

**Current Behavior:**
- Table has 4 columns: Timestamp, Level, Message, Source
- No way to reference specific line numbers
- Difficult to discuss specific log entries ("line 42 says...")

**Proposed Behavior:**
- Add **Line #** column as the first (leftmost) column
- Shows the 1-based line number in the **original file** (not filtered index)
- 5 columns total: **Line #**, Timestamp, Level, Message, Source
- Column properties:
  - Width: 60-80px (fixed)
  - Alignment: Right-aligned
  - Color: Dimmed/gray text
  - Non-selectable for copying (or optionally include)

**Implementation Notes:**
- Modify `LogEntry` dataclass to include `line_number: int` field
- Parser sets line number during parsing (1-based, increments per line read)
- `LogTableModel` adds new column at index 0
- Existing column indices shift: Timestamp=1, Level=2, Message=3, Source=4
- Update `COL_*` constants in `LogTableModel`
- When copying rows (Ctrl+C), optionally include line number in format:
  - Current: `[timestamp][LEVEL]: message | source`
  - Optional: `Line 42: [timestamp][LEVEL]: message | source`

**Visual Example:**
```
+--------+-------------+--------+---------------------------+------------------+
| Line # | Timestamp   | Level  | Message                   | Source           |
+--------+-------------+--------+---------------------------+------------------+
|     42 | 16:29:40.31 | DEBUG  | Vulkan loader version...  | Vulkan.cpp:92    |
|     43 | 16:29:40.58 | INFO   | Supported instance ext... | Vulkan.cpp:106   |
|    102 | 16:29:41.15 | ERROR  | Failed to create surface  | Vulkan.cpp:156   |
+--------+-------------+--------+---------------------------+------------------+
```

**Benefits:**
- Easy to reference specific log entries
- Matches how developers think about logs ("check line 42")
- Professional log viewer feature
- Helps with debugging discussions

---

### Change D: Jump to Line Number

**Current Behavior:**
- No way to quickly navigate to a specific line
- Must scroll manually through potentially thousands of entries
- Search only works on message content

**Proposed Behavior:**
- Add "Jump to Line:" input box in search/filter pane
- Layout: Bottom pane has two rows:
  - **Row 1**: Search: [___input___] | Jump to Line: [___] [Go]
  - **Row 2**: Filters: [ ] DEBUG [ ] INFO [ ] WARN [ ] ERROR
- Input accepts line numbers (1-based)
- Pressing Enter or clicking "Go" button:
  1. Clears all active filters
  2. Clears search text
  3. Shows all entries
  4. Scrolls to and selects the specified line number
  5. Status message: "Jumped to line 42"
- If line number is invalid:
  - Show error: "Line 42 not found" or "Invalid line number"
  - Don't clear filters/search

**Implementation Notes:**
- Add `QLineEdit` for line number input (width: ~80px)
- Add "Go" button next to it (width: ~40px)
- Validate input: must be positive integer
- Line number is the **original file line**, not filtered index
- Algorithm:
  ```python
  def jump_to_line(self, line_number: int):
      # Find entry with matching line_number
      for i, entry in enumerate(self._log_entries):
          if entry.line_number == line_number:
              # Clear filters/search to ensure visibility
              self._clear_all_filters()
              # Select and scroll to row
              self._log_table.selectRow(i)
              self._log_table.scrollTo(model_index)
              return True
      return False  # Line not found
  ```
- Add helper method `_clear_all_filters()`:
  - Unchecks all filter checkboxes
  - Clears search input
  - Calls `_apply_filters()` to show all entries
- Alternative: Use `Ctrl+G` or `Ctrl+L` as keyboard shortcut

**Visual Example:**
```
+---------------------------------------------------------------+
| Search: [vulkan____________] | Jump to Line: [42___] [Go]    |
| Filters: [ ] DEBUG  [x] INFO  [ ] WARN  [x] ERROR            |
+---------------------------------------------------------------+
```

**Benefits:**
- Quick navigation to specific log entries
- Essential for debugging workflows
- Matches behavior of text editors (Ctrl+G to go to line)
- Automatically handles filter conflicts

---

## Additional Considerations

### Updated File Structure
```
python/
  log_entry.py       - Add line_number field to LogEntry
  log_parser.py      - Track line numbers during parsing
  log_table_model.py - Add Line # column
  main_window.py     - Implement all UI changes
  config.py          - Add last_directory support
```

### Configuration Changes
- **Old**: Save last file path
- **New**: Save last directory AND last file path
- Format (simple text file, one value per line):
  ```
  /path/to/logs/directory
  /path/to/logs/directory/helix.log
  ```

### Layout Changes

**Before (Current):**
```
+---------------------------------------------------------------+
| File: [________________input_________________] [Open] [Copy]  |
| Status: Ready                                                 |
+---------------------------------------------------------------+
| Timestamp | Level | Message | Source                          |
| (table content)                                               |
| Showing 1,234 of 5,678 entries                                |
+---------------------------------------------------------------+
| Search: [______________] | Filters: [ ] DEBUG [ ] INFO ...   |
+---------------------------------------------------------------+
```

**After (Proposed):**
```
+---------------------------------------------------------------+
| File  Help                                    [Menu Bar]       |
+---------------------------------------------------------------+
| Line# | Timestamp | Level | Message | Source                  |
| (table content)                                               |
+---------------------------------------------------------------+
| Search: [__________] | Jump to Line: [___] [Go]              |
| Filters: [ ] DEBUG  [ ] INFO  [ ] WARN  [ ] ERROR            |
+---------------------------------------------------------------+
| Ready | File: helix.log | 1,271 entries | Line 42 of 1,271   |
+---------------------------------------------------------------+
```

### Backward Compatibility
- Old config files (single line) still work (use as file path, extract directory)
- New format is two lines (directory, then file path)
- Graceful degradation if config is missing/corrupted

### Testing Requirements
- File dialog opens to correct directory
- Status bar sections update correctly
- Line numbers match original file (not filtered indices)
- Jump to line works with/without filters active
- Jump to line clears filters when needed
- Invalid line numbers show error without breaking UI
- Ctrl+R reload maintains line numbers
- Config saves/loads directory correctly

---

## Implementation Priority

1. **Change B (Status Bar)** - Foundation for other changes
2. **Change A (File Dialog)** - Removes top pane
3. **Change C (Line Numbers)** - Data model update
4. **Change D (Jump to Line)** - Feature on top of line numbers

## Migration Notes

- Users will need to "Open" their file again (old file path input removed)
- Config file format changes (add migration logic)
- All existing features continue to work
- No changes to log file format or parsing logic

---

## Success Criteria

✅ No file path input field visible
✅ File → Open uses native file dialog
✅ Status bar shows: status, file, entry count, line info
✅ Table has Line # as first column
✅ Line numbers match original file
✅ Jump to Line input works with Enter or Go button
✅ Jump to Line clears filters when needed
✅ All existing features still work (filters, search, copy, reload)
✅ Professional, modern GUI appearance

---

## Future Enhancements (Not in Scope)

These are potential future improvements, not part of this spec:
- Recent files list (File → Recent)
- Bookmarks for important lines
- Split view (compare two log files)
- Export filtered results
- Dark mode theme
- Column sorting
- Custom column ordering
- Live tail mode (watch file for changes)
