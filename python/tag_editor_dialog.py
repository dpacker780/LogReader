"""
Tag Editor Dialog for LogReader application.

This module provides a dialog for customizing log level tags:
- Add new tags
- Edit existing tags (name and color)
- Remove tags
- Reset to defaults
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QColorDialog, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from python.config import ConfigManager, LogTag


class TagEditorDialog(QDialog):
    """Dialog for editing log level tags."""

    def __init__(self, parent=None):
        """
        Initialize the Tag Editor dialog.

        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)

        self.setWindowTitle("Tag Editor")
        self.resize(600, 400)

        # Local copy of tags (not saved until OK is clicked)
        self._tags: List[LogTag] = []
        self._load_tags()

        # Setup UI
        self._setup_ui()

    def _load_tags(self):
        """Load tags from config into local copy."""
        self._tags = [
            LogTag(tag.name, tag.color, tag.enabled, tag.order)
            for tag in ConfigManager.load_tags()
        ]

    def _setup_ui(self):
        """Create and layout all UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Customize log level tags and colors. "
            "Changes will be saved when you click OK."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Tag table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Tag Name", "Color", "Preview"])

        # Configure columns
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Populate table
        self._refresh_table()

        layout.addWidget(self._table)

        # Button row
        button_row = QHBoxLayout()

        add_btn = QPushButton("Add Tag")
        add_btn.clicked.connect(self._on_add_tag)
        button_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit Tag")
        edit_btn.clicked.connect(self._on_edit_tag)
        button_row.addWidget(edit_btn)

        remove_btn = QPushButton("Remove Tag")
        remove_btn.clicked.connect(self._on_remove_tag)
        button_row.addWidget(remove_btn)

        button_row.addStretch()

        layout.addLayout(button_row)

        # Reset and OK/Cancel buttons
        bottom_row = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset)
        bottom_row.addWidget(reset_btn)

        bottom_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        bottom_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_btn)

        layout.addLayout(bottom_row)

    def _refresh_table(self):
        """Refresh the tag table with current tags."""
        self._table.setRowCount(len(self._tags))

        for row, tag in enumerate(self._tags):
            # Tag name
            name_item = QTableWidgetItem(tag.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 0, name_item)

            # Color swatch (clickable)
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(tag.color))
            color_item.setText(tag.color)
            color_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 1, color_item)

            # Preview (tag name in color)
            preview_item = QTableWidgetItem(tag.name)
            preview_item.setForeground(QColor(tag.color))
            preview_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 2, preview_item)

        # Connect double-click to edit
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _on_cell_double_clicked(self, row: int, col: int):
        """Handle double-click on table cell."""
        if col == 1:
            # Double-clicked color column - open color picker
            self._edit_tag_color(row)
        else:
            # Double-clicked name or preview - edit tag
            self._on_edit_tag()

    def _on_add_tag(self):
        """Handle Add Tag button click."""
        dialog = AddEditTagDialog(self, "Add Tag")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tag_name, tag_color = dialog.get_result()

            # Check for duplicate
            if any(t.name.upper() == tag_name.upper() for t in self._tags):
                QMessageBox.warning(
                    self,
                    "Duplicate Tag",
                    f"Tag '{tag_name}' already exists."
                )
                return

            # Add new tag
            new_tag = LogTag(
                name=tag_name.upper(),
                color=tag_color,
                enabled=True,
                order=len(self._tags)
            )
            self._tags.append(new_tag)
            self._refresh_table()

    def _on_edit_tag(self):
        """Handle Edit Tag button click."""
        current_row = self._table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a tag to edit."
            )
            return

        tag = self._tags[current_row]

        dialog = AddEditTagDialog(self, "Edit Tag", tag.name, tag.color)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_color = dialog.get_result()

            # Check for duplicate (excluding current tag)
            if new_name.upper() != tag.name.upper():
                if any(t.name.upper() == new_name.upper() for t in self._tags):
                    QMessageBox.warning(
                        self,
                        "Duplicate Tag",
                        f"Tag '{new_name}' already exists."
                    )
                    return

            # Update tag
            tag.name = new_name.upper()
            tag.color = new_color
            self._refresh_table()

    def _edit_tag_color(self, row: int):
        """
        Edit the color of a specific tag.

        Args:
            row: Row index in the table
        """
        if row < 0 or row >= len(self._tags):
            return

        tag = self._tags[row]
        initial_color = QColor(tag.color)

        color = QColorDialog.getColor(initial_color, self, "Choose Tag Color")
        if color.isValid():
            tag.color = color.name()  # Returns hex format #RRGGBB
            self._refresh_table()

    def _on_remove_tag(self):
        """Handle Remove Tag button click."""
        current_row = self._table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a tag to remove."
            )
            return

        tag = self._tags[current_row]

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove tag '{tag.name}'?\n\n"
            f"This will affect filtering and display of log entries with this tag.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self._tags[current_row]
            self._refresh_table()

    def _on_reset(self):
        """Handle Reset to Defaults button click."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all tags to defaults?\n\n"
            "This will remove all custom tags and restore the original 6 tags.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reload default tags
            from python.config import AppConfig
            self._tags = AppConfig._default_tags()
            self._refresh_table()

    def get_tags(self) -> List[LogTag]:
        """
        Get the current list of tags.

        Returns:
            List of LogTag objects (only valid if dialog was accepted)
        """
        return self._tags


class AddEditTagDialog(QDialog):
    """Dialog for adding or editing a single tag."""

    def __init__(self, parent=None, title: str = "Add/Edit Tag",
                 initial_name: str = "", initial_color: str = "#808080"):
        """
        Initialize the Add/Edit Tag dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            initial_name: Initial tag name (for edit mode)
            initial_color: Initial color (hex format)
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(350, 200)

        self._color = initial_color

        # Setup UI
        layout = QVBoxLayout(self)

        # Tag name input
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Tag Name:"))
        self._name_input = QLineEdit(initial_name)
        self._name_input.setPlaceholderText("e.g., DEBUG, VERBOSE, FATAL")
        name_row.addWidget(self._name_input)
        layout.addLayout(name_row)

        # Color picker
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))

        self._color_preview = QLabel()
        self._color_preview.setFixedSize(50, 25)
        self._color_preview.setStyleSheet(f"background-color: {self._color}; border: 1px solid black;")
        color_row.addWidget(self._color_preview)

        choose_color_btn = QPushButton("Choose...")
        choose_color_btn.clicked.connect(self._on_choose_color)
        color_row.addWidget(choose_color_btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        # Preview
        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Preview:"))
        self._preview_label = QLabel(initial_name if initial_name else "TAG NAME")
        self._preview_label.setStyleSheet(f"color: {self._color}; font-weight: bold;")
        preview_row.addWidget(self._preview_label)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        # Update preview when name changes
        self._name_input.textChanged.connect(self._update_preview)

        layout.addStretch()

        # OK/Cancel buttons
        button_row = QHBoxLayout()
        button_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        layout.addLayout(button_row)

    def _on_choose_color(self):
        """Handle Choose Color button click."""
        initial_color = QColor(self._color)
        color = QColorDialog.getColor(initial_color, self, "Choose Tag Color")

        if color.isValid():
            self._color = color.name()
            self._color_preview.setStyleSheet(f"background-color: {self._color}; border: 1px solid black;")
            self._update_preview()

    def _update_preview(self):
        """Update the preview label."""
        name = self._name_input.text() if self._name_input.text() else "TAG NAME"
        self._preview_label.setText(name.upper())
        self._preview_label.setStyleSheet(f"color: {self._color}; font-weight: bold;")

    def accept(self):
        """Validate and accept the dialog."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Name", "Tag name cannot be empty.")
            return

        # Validate tag name (alphanumeric + underscore only)
        if not all(c.isalnum() or c == '_' for c in name):
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Tag name can only contain letters, numbers, and underscores."
            )
            return

        super().accept()

    def get_result(self) -> tuple[str, str]:
        """
        Get the tag name and color.

        Returns:
            Tuple of (tag_name, hex_color)
        """
        return self._name_input.text().strip().upper(), self._color
