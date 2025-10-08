"""
Message Detail Dialog for LogReader application.

This module provides a dialog for displaying full log message details
that may be too long to view comfortably in the table.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from python.log_entry import LogEntry


class MessageDetailDialog(QDialog):
    """Dialog for displaying full log message details."""

    def __init__(self, entry: LogEntry, parent=None):
        """
        Initialize the Message Detail dialog.

        Args:
            entry: LogEntry to display
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)

        self.setWindowTitle("Message Details")
        self.resize(800, 400)

        # Setup UI
        self._setup_ui(entry)

    def _setup_ui(self, entry: LogEntry):
        """Create and layout all UI components."""
        layout = QVBoxLayout(self)

        # Header: Show line number, timestamp, level, source
        header_text = (
            f"<b>Line {entry.line_number}</b> | "
            f"{entry.timestamp} | "
            f"<span style='color: {self._get_level_color(entry.level.value)};'>{entry.level.value}</span>"
        )
        if entry.source_file or entry.function_name:
            header_text += f" | {entry.format_source_info()}"

        header_label = QLabel(header_text)
        header_label.setTextFormat(Qt.TextFormat.RichText)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)

        # Message text area (scrollable, read-only, monospace)
        self._text_edit = QTextEdit()
        self._text_edit.setPlainText(entry.message)
        self._text_edit.setReadOnly(True)

        # Set monospace font for consistent display
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self._text_edit.setFont(font)

        layout.addWidget(self._text_edit)

        # Button row
        button_row = QHBoxLayout()
        button_row.addStretch()

        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        button_row.addWidget(copy_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

    def _get_level_color(self, level_name: str) -> str:
        """Get the color for a log level from config."""
        from python.config import ConfigManager
        return ConfigManager.get_tag_color(level_name, "#FFFFFF")

    def _copy_to_clipboard(self):
        """Copy the full message text to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text_edit.toPlainText())

        # Update button text briefly to show it worked
        sender = self.sender()
        if sender:
            original_text = sender.text()
            sender.setText("Copied!")
            # Reset after 1 second
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: sender.setText(original_text))
