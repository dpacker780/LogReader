# LogReader v1.3 Release Notes

**Release Date**: January 2025

## Overview

Version 1.3 introduces **Search Navigation** - a major UX improvement that transforms how you interact with search results. Instead of filtering entries out of view, search now highlights all matches and provides Previous/Next navigation, keeping full context visible while you explore results.

This release also includes significant UI layout improvements for better space utilization and visual clarity.

---

## Major Features

### 🔍 Search Navigation (Replaces Search Filtering)

**The Problem**: In v1.2, searching would hide non-matching entries, losing important context around your search results.

**The Solution**: v1.3 keeps all entries visible and adds navigation:

- **All matches highlighted** with theme-aware background color
- **Active match selected** using Qt's native row selection (blue/gray)
- **Previous/Next buttons** to navigate through results
- **Result counter** shows "Result X of Y"
- **Keyboard shortcuts**: `Ctrl+P` (Previous), `Ctrl+N` (Next)
- **Circular navigation**: Wraps from last to first result

**Why This Matters**:
- See what happened before/after each match
- Maintain visual context while exploring results
- Faster navigation with keyboard shortcuts
- Better understanding of log sequences

**Example Workflow**:
1. Search for "error"
2. See all log entries (matches highlighted)
3. Use Next/Previous to jump between error occurrences
4. See surrounding context for each error
5. No more filter toggling to see what came before!

### 🎨 Optimized UI Layout

**Two-Section Side-by-Side Design**:

**Section 1 (Left)** - Search & Navigation (compact, 250-300px):
- Search input field
- Previous/Next buttons and result counter directly below
- Tight spacing - "Search:" label no longer wastes space

**Section 2 (Right)** - Filters & Controls (stretches to fill space):
- File dropdown + Jump to Line + Reset All button
- Filter checkboxes below
- More room for tags and controls

**Visual Improvements**:
- ✅ Clean vertical separator (no distracting box outlines)
- ✅ 20 pixels taller for better breathing room (120px total)
- ✅ Compact left section gives more space to filters/controls
- ✅ Intuitive grouping of related controls
- ✅ Better horizontal space utilization

### 🖱️ Double-Click Behavior Change

**Old**: Double-click cleared all filters (could lose your search results)
**New**: Double-click opens message detail dialog (same as Ctrl+M)

**Why**: More consistent and useful - see full message text without losing your search/filter state.

---

## Detailed Changes

### Search Navigation Features

| Feature | Description |
|---------|-------------|
| **Theme-Aware Highlighting** | Dark theme: #2A4A6A, Light theme: #D0E8FF |
| **Row Selection** | Active result uses Qt's native selection (blue highlight) |
| **Result Counter** | "Result X of Y" in light green next to buttons |
| **Previous Button** | Navigate to previous match (Ctrl+P) |
| **Next Button** | Navigate to next match (Ctrl+N) |
| **Circular Navigation** | Wraps from end to beginning and vice versa |
| **Auto-Scroll** | Centers selected result in viewport |
| **Search Respects Filters** | Only searches within filtered entries |

### UI Layout Changes

| Change | Before | After |
|--------|--------|-------|
| **Layout Direction** | Stacked vertically | Side-by-side horizontally |
| **Section 1 Width** | 400-500px | 250-300px |
| **Section 2 Width** | Fixed | Stretches to fill space |
| **Frame Height** | 100px | 120px (+20px) |
| **Visual Separator** | Box outlines around each section | Clean vertical line |
| **Search Label Spacing** | 60px minimum width (wasteful) | Auto-sized (tight) |
| **Navigation Alignment** | 60px offset | Flush left |

### Keyboard Shortcuts (New/Updated)

| Shortcut | Action | Notes |
|----------|--------|-------|
| **Ctrl+N** | Next search result | NEW - Circular navigation |
| **Ctrl+P** | Previous search result | NEW - Circular navigation |
| **Double-Click** | Show message detail dialog | CHANGED - Was "clear filters" |
| **Enter** | Execute search | Existing - In search field |

---

## Technical Details

### Search Implementation

**v1.2 (Old Behavior)**:
```
Search "error" → Filters entries → Only shows matches → Context lost
```

**v1.3 (New Behavior)**:
```
Search "error" → Finds matches → Highlights all → Navigate with Prev/Next → Context preserved
```

**Code Changes**:
- `_apply_filters()`: Search no longer filters entries, calls `_perform_search_navigation()`
- `_perform_search_navigation()`: Finds matches, highlights rows, selects first result
- `_on_search_prev()` / `_on_search_next()`: Navigate through `_search_result_indices`
- `LogTableModel.set_search_highlights()`: BackgroundRole highlighting for matches
- `LogTableModel` stores: `_search_highlight_rows`, `_current_search_row`, `_all_matches_color`

### UI Architecture

**Layout Structure**:
```
QHBoxLayout (main horizontal layout)
├── QFrame (Section 1 - Search & Navigation)
│   ├── QVBoxLayout
│   │   ├── Row 1: Search label + input field
│   │   └── Row 2: Prev button + Next button + Result counter
│   └── Width: 250-300px (compact, no stretch)
├── QFrame (Vertical separator - VLine)
└── QFrame (Section 2 - Filters & Controls)
    ├── QVBoxLayout
    │   ├── Row 1: File dropdown + Jump to Line + Reset All
    │   └── Row 2: Filter checkboxes
    └── Width: Stretches (stretch=1)
```

### Theme Detection

Uses Qt palette to detect dark/light theme:
```python
def _get_search_highlight_colors(self):
    palette = self.palette()
    base_color = palette.color(palette.ColorRole.Base)
    is_dark = base_color.lightness() < 128

    if is_dark:
        return "#2A4A6A", "#3A5A8A"  # Dark theme blues
    else:
        return "#D0E8FF", "#B0D0FF"  # Light theme blues
```

---

## Migration Guide

### For Users

**No action required** - v1.3 is a drop-in replacement.

**Behavior Changes to Note**:

1. **Search now navigates** instead of filtering:
   - You'll see all log entries (not just matches)
   - Use Prev/Next buttons or Ctrl+P/Ctrl+N to jump between results
   - All matches are subtly highlighted in light blue

2. **Double-click changed**:
   - No longer clears filters
   - Now opens message detail dialog (same as Ctrl+M)
   - Use "Reset All" button to clear filters manually

3. **UI layout changed**:
   - Controls reorganized into two side-by-side sections
   - More compact search section on left
   - More room for filters on right

### For Developers

**API Changes** (internal):

```python
# New methods in MainWindow
def _get_search_highlight_colors(self) -> Tuple[str, str]
def _perform_search_navigation(self, search_term: str, filtered_indices: List[int])
def _clear_search_navigation(self)
def _on_search_prev(self)
def _on_search_next(self)

# New state variables in MainWindow
self._search_result_indices: List[int]  # Row indices of matches
self._current_search_index: int         # Current position in results
self._search_prev_button: QPushButton
self._search_next_button: QPushButton
self._search_counter_label: QLabel

# New methods in LogTableModel
def set_search_highlights(self, highlight_rows, current_row, all_color, current_color)
def clear_search_highlights(self)

# New state in LogTableModel
self._search_highlight_rows: List[int]
self._current_search_row: int
self._all_matches_color: str
self._current_match_color: str
```

---

## Performance

**Search Navigation**:
- **Search time**: <1ms for 1,000+ entries (same as v1.2)
- **Navigation**: Instant (just selects and scrolls to row)
- **Highlight rendering**: Handled by Qt's BackgroundRole (efficient)
- **Memory**: Stores only row indices (negligible overhead)

**No Performance Regression**: All v1.2 performance characteristics maintained.

---

## Known Issues

None reported at release time.

---

## Future Enhancements (v1.4+)

Based on v1.3 foundation:

- **Regex Search**: Pattern-based matching for power users
- **Multi-Field Search**: Search across timestamp, level, source, etc.
- **Search History**: Recent searches dropdown
- **Highlight Customization**: User-configurable highlight colors
- **Bookmark Integration**: Mark important search results
- **Export Search Results**: Save matches to file

---

## Acknowledgments

Special thanks to:
- Beta testers who identified the need for search navigation
- Users who requested better UI organization
- Qt framework for excellent theme integration

---

## Getting Started with v1.3

### Search Navigation Tutorial

1. **Open a log file** (Ctrl+O)
2. **Type a search term** (e.g., "error")
3. **Press Enter** - All entries remain visible, matches highlighted
4. **Click "Next ▶"** or press Ctrl+N to jump to next match
5. **Click "◀ Prev"** or press Ctrl+P to go back
6. **Observe the counter** - "Result X of Y" shows your position
7. **See context** - All surrounding entries visible!

### UI Layout Tour

**Left Section** (Compact):
- Search input + magnifying glass icon
- Previous/Next buttons directly below
- Result counter in light green

**Right Section** (Spacious):
- File filter dropdown (filter by source file)
- Jump to Line field + Go button
- Reset All button (clears everything)
- Filter checkboxes with optional counts

---

## Version Comparison

| Feature | v1.2 | v1.3 |
|---------|------|------|
| **Search Behavior** | Filters entries | Highlights + navigates |
| **Search Context** | Hidden | Always visible |
| **Search Navigation** | None | Prev/Next buttons + shortcuts |
| **Result Counter** | None | "Result X of Y" |
| **Double-Click** | Clear filters | Show message details |
| **UI Layout** | Stacked sections | Side-by-side sections |
| **Search Section Width** | ~400px | ~275px (compact) |
| **Visual Separator** | Box outlines | Clean vertical line |
| **Frame Height** | 100px | 120px |

---

## Download & Install

### Requirements
- Python 3.10+
- PyQt6 6.6.0+

### Quick Install
```bash
# Clone repository
git clone https://github.com/dpacker780/LogReader.git
cd LogReader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run
python python/main.py
```

### Upgrade from v1.2
```bash
# Update repository
git pull origin master

# Existing venv and config work as-is
python python/main.py
```

---

## Documentation

- **[README.md](README.md)** - Full feature guide
- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user manual
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 5-minute quick start
- **[RELEASE_v1.2.md](RELEASE_v1.2.md)** - Previous version notes

---

## Support

- **Issues**: https://github.com/dpacker780/LogReader/issues
- **Discussions**: https://github.com/dpacker780/LogReader/discussions

---

**Enjoy the improved search experience in v1.3!**
