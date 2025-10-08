"""
Table model for displaying log entries in Qt's Model/View architecture.

This module provides a custom QAbstractTableModel that efficiently displays
log entries with color coding based on log levels.
"""

import sys
from pathlib import Path
from typing import List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QColor, QBrush

try:
    from .log_entry import LogEntry, LogLevel
    from .config import ConfigManager
except ImportError:
    from python.log_entry import LogEntry, LogLevel
    from python.config import ConfigManager


class LogTableModel(QAbstractTableModel):
    """
    Custom table model for efficient log entry display.

    Uses Qt's Model/View pattern to efficiently display large numbers of log entries.
    Supports filtering by maintaining a separate list of filtered indices to avoid
    copying the entire dataset.

    Features:
    - Color-coded log levels
    - Efficient filtering using index list
    - Four columns: Timestamp, Level, Message, Source
    """

    # Column indices
    COL_LINE_NUMBER = 0
    COL_TIMESTAMP = 1
    COL_LEVEL = 2
    COL_MESSAGE = 3
    COL_FILE = 4
    COL_FUNCTION = 5
    COL_LINE = 6

    # Column headers
    HEADERS = ["Line #", "Timestamp", "Level", "Message", "File", "Function", "Line"]

    def __init__(self, parent=None):
        """
        Initialize the table model.

        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)

        # All log entries (unfiltered)
        self._entries: List[LogEntry] = []

        # Indices of entries to display (after filtering/searching)
        self._filtered_indices: List[int] = []

    def set_entries(self, entries: List[LogEntry]):
        """
        Set the log entries to display.

        This replaces all existing entries and resets the model.

        Args:
            entries: List of LogEntry objects to display
        """
        self.beginResetModel()

        self._entries = entries
        # Initially, show all entries (no filter)
        self._filtered_indices = list(range(len(entries)))

        self.endResetModel()

    def set_filtered_indices(self, indices: List[int]):
        """
        Set which entries to display based on filtering/searching.

        This allows efficient filtering without copying the entire entry list.

        Args:
            indices: List of indices into self._entries to display
        """
        self.beginResetModel()
        self._filtered_indices = indices
        self.endResetModel()

    def get_entry(self, row: int) -> Optional[LogEntry]:
        """
        Get the log entry at the specified row.

        Args:
            row: Row index in the filtered view

        Returns:
            LogEntry object or None if row is invalid
        """
        if 0 <= row < len(self._filtered_indices):
            entry_index = self._filtered_indices[row]
            if 0 <= entry_index < len(self._entries):
                return self._entries[entry_index]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Return the number of rows (filtered entries) in the model.

        Args:
            parent: Parent index (unused for table models)

        Returns:
            Number of rows to display
        """
        if parent.isValid():
            return 0
        return len(self._filtered_indices)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Return the number of columns in the model.

        Args:
            parent: Parent index (unused for table models)

        Returns:
            Number of columns (always 4)
        """
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Return data for the specified cell and role.

        Args:
            index: Cell index (row, column)
            role: Data role (DisplayRole, ForegroundRole, etc.)

        Returns:
            Data for the specified role, or None if not available
        """
        if not index.isValid():
            return QVariant()

        row = index.row()
        col = index.column()

        # Get the log entry for this row
        entry = self.get_entry(row)
        if entry is None:
            return QVariant()

        # DisplayRole: Return the text to display
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_LINE_NUMBER:
                return str(entry.line_number)
            elif col == self.COL_TIMESTAMP:
                return entry.timestamp
            elif col == self.COL_LEVEL:
                return entry.level.value
            elif col == self.COL_MESSAGE:
                return entry.message
            elif col == self.COL_FILE:
                return entry.source_file
            elif col == self.COL_FUNCTION:
                return entry.source_function
            elif col == self.COL_LINE:
                return str(entry.source_line)

        # ForegroundRole: Return the text color
        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == self.COL_LINE_NUMBER:
                # Dimmed gray for line numbers
                return QBrush(QColor(128, 128, 128))
            elif col == self.COL_LEVEL:
                # Get tag color from config (dynamic tags)
                hex_color = ConfigManager.get_tag_color(entry.level.value, "#FFFFFF")
                color = QColor(hex_color)
                return QBrush(color)
            elif col == self.COL_MESSAGE:
                # Get message color from tag config
                tag = ConfigManager.get_or_create_tag(entry.level.value)
                if tag.message_match_tag:
                    # Use tag color for message
                    msg_color = tag.color
                else:
                    # Use custom message color
                    msg_color = tag.message_color
                return QBrush(QColor(msg_color))

        # TextAlignmentRole: Right-align line numbers and source line, center-align level
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == self.COL_LINE_NUMBER or col == self.COL_LINE:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            elif col == self.COL_LEVEL:
                return Qt.AlignmentFlag.AlignCenter

        # ToolTipRole: Show full message text on hover for Message column
        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == self.COL_MESSAGE:
                # Return full message text as tooltip with max width
                # Use HTML with a div to control width (approximately 120 characters)
                message = entry.message.replace('<', '&lt;').replace('>', '&gt;')  # Escape HTML
                return f'<div style="max-width: 900px; white-space: pre-wrap;">{message}</div>'

        return QVariant()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """
        Return header data for the specified section.

        Args:
            section: Column or row index
            orientation: Horizontal (column) or Vertical (row)
            role: Data role

        Returns:
            Header text or None
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.HEADERS):
                    return self.HEADERS[section]

        return QVariant()

    def get_total_entry_count(self) -> int:
        """
        Get the total number of entries (unfiltered).

        Returns:
            Total number of log entries
        """
        return len(self._entries)

    def get_filtered_entry_count(self) -> int:
        """
        Get the number of filtered entries (currently displayed).

        Returns:
            Number of filtered entries
        """
        return len(self._filtered_indices)

    def clear(self):
        """Clear all entries from the model."""
        self.beginResetModel()
        self._entries.clear()
        self._filtered_indices.clear()
        self.endResetModel()
