"""
Main window for LogReader application.

This module defines the MainWindow class which contains all UI components
and handles user interactions.
"""

import sys
import threading
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QTableView,
    QCheckBox, QFrame, QSizePolicy, QHeaderView, QMessageBox, QFileDialog, QApplication, QDialog, QComboBox
)
# QFrame already imported above
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut, QAction

from python.log_entry import LogLevel, LogEntry
from python.log_table_model import LogTableModel
from python.log_parser import LogParser
from python.config import ConfigManager


class ParserSignals(QObject):
    """
    Signals for communicating from parser thread to UI thread.

    Qt signals are thread-safe and automatically marshal calls to the main thread.
    """
    # Signal: progress_update(status_message, current_entries)
    progress_update = pyqtSignal(str, list)


class MainWindow(QMainWindow):
    """
    Main application window for LogReader.

    Provides a three-pane interface:
    - Top: File controls (path input, open button, copy button, status)
    - Middle: Log entries table (scrollable, virtualized)
    - Bottom: Search and filter controls
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Window properties
        self.setWindowTitle("LogReader")
        self.setMinimumSize(1024, 768)
        self.resize(1200, 800)

        # Data storage
        self._log_entries: List[LogEntry] = []
        self._entries_lock = threading.Lock()
        self._current_file_path: str = ""  # Track currently loaded file

        # File monitoring
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.fileChanged.connect(self._on_file_changed)

        # Parser and signals
        self._parser = LogParser()
        self._parser_signals = ParserSignals()
        self._parser_signals.progress_update.connect(self._on_parser_progress)

        # UI components will be created in _setup_ui
        self._file_input: QLineEdit = None  # Hidden, used for internal tracking
        self._search_input: QLineEdit = None
        self._file_filter_combo: QComboBox = None  # File filter dropdown
        self._jump_input: QLineEdit = None
        self._jump_button: QPushButton = None
        self._log_table: QTableView = None
        self._log_model: LogTableModel = None
        self._filter_checkboxes: Dict[str, QCheckBox] = {}  # tag_name -> checkbox
        self._filter_count_labels: Dict[str, QLabel] = {}  # tag_name -> count label
        self._filter_layout: QHBoxLayout = None  # Store reference to filter row layout

        # Status bar widgets
        self._status_message: QLabel = None
        self._status_file: QLabel = None
        self._status_entries: QLabel = None
        self._status_line: QLabel = None

        # Setup the user interface
        self._setup_ui()

        # Setup status bar
        self._setup_statusbar()

        # Setup menubar
        self._setup_menubar()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Auto-load last file on startup
        last_file = ConfigManager.load_last_file_path()
        self._file_input.setText(last_file)

        # If last file exists, auto-load it
        if last_file and Path(last_file).exists():
            self._auto_load_last_file(last_file)

    def _setup_ui(self):
        """Create and layout all UI components."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Initialize file input (hidden, used for internal tracking)
        self._create_file_controls_pane()

        # Add two panes (removed top file controls pane)
        main_layout.addWidget(self._create_log_display_pane(), stretch=1)
        main_layout.addWidget(self._create_search_filter_pane())

    def _create_file_controls_pane(self) -> QFrame:
        """
        Create the top pane - now removed for cleaner UI.

        File opening is done via File menu or Ctrl+O.
        Returns None since this pane is no longer used.
        """
        # Keep _file_input for internal tracking (needed for reload)
        # but don't display it
        self._file_input = QLineEdit()
        self._file_input.setVisible(False)

        return None

    def _create_log_display_pane(self) -> QFrame:
        """
        Create the middle pane with log entries table.

        Returns:
            QFrame containing the log table and entry count
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Create table model
        self._log_model = LogTableModel()

        # Log table view
        self._log_table = QTableView()
        self._log_table.setModel(self._log_model)

        # Configure table appearance
        self._log_table.setAlternatingRowColors(True)
        self._log_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._log_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)  # Allow multi-select
        self._log_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._log_table.verticalHeader().setVisible(False)

        # Always show vertical scrollbar to prevent table jumping
        self._log_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Make clicking anywhere on the row select the entire row
        self._log_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        header = self._log_table.horizontalHeader()
        header.setHighlightSections(False)

        # Set column widths
        header = self._log_table.horizontalHeader()

        # Fixed size columns
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Entry #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Timestamp
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Level
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Line

        # Stretch column (Message takes all available space)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Message

        # Resizable columns (File, Function)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # File
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Function

        # Set initial widths for fixed and interactive columns
        self._log_table.setColumnWidth(0, 70)   # Entry #
        self._log_table.setColumnWidth(1, 120)  # Timestamp
        self._log_table.setColumnWidth(2, 80)   # Level
        self._log_table.setColumnWidth(4, 180)  # File (resizable)
        self._log_table.setColumnWidth(5, 150)  # Function (resizable)
        self._log_table.setColumnWidth(6, 60)   # Line
        # Note: Message (column 3) will stretch automatically to fill remaining space

        # Set font for better readability
        table_font = QFont("Consolas", 9)
        if not table_font.exactMatch():
            table_font = QFont("Courier New", 9)
        self._log_table.setFont(table_font)

        # Connect double-click to clear filters and show context
        self._log_table.doubleClicked.connect(self._on_table_double_click)

        layout.addWidget(self._log_table)

        return frame

    def _create_search_filter_pane(self) -> QFrame:
        """
        Create the bottom pane with search and filter controls.

        Returns:
            QFrame containing search input and level filter checkboxes
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setMaximumHeight(100)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # First row: Search input and Jump to Line
        search_row = QHBoxLayout()

        search_label = QLabel("Search:")
        search_label.setMinimumWidth(60)
        search_row.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("search term")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_input, stretch=1)

        # Spacer
        search_row.addSpacing(20)

        # File filter dropdown
        file_label = QLabel("File:")
        search_row.addWidget(file_label)

        self._file_filter_combo = QComboBox()
        self._file_filter_combo.setMinimumWidth(200)
        self._file_filter_combo.addItem("All")
        self._file_filter_combo.currentTextChanged.connect(self._on_file_filter_changed)
        search_row.addWidget(self._file_filter_combo)

        # Spacer
        search_row.addSpacing(20)

        # Jump to Line controls
        jump_label = QLabel("Jump to Line:")
        search_row.addWidget(jump_label)

        self._jump_input = QLineEdit()
        self._jump_input.setPlaceholderText("#")
        self._jump_input.setMaximumWidth(80)
        self._jump_input.returnPressed.connect(self._on_jump_clicked)
        search_row.addWidget(self._jump_input)

        self._jump_button = QPushButton("Go")
        self._jump_button.setMaximumWidth(50)
        self._jump_button.clicked.connect(self._on_jump_clicked)
        search_row.addWidget(self._jump_button)

        layout.addLayout(search_row)

        # Second row: Filter checkboxes
        self._filter_layout = QHBoxLayout()
        self._filter_layout.setSpacing(0)  # Remove spacing between widgets for tight count labels
        self._build_filter_ui()
        layout.addLayout(self._filter_layout)

        return frame

    def _build_filter_ui(self):
        """Build the filter checkboxes UI from current tags."""
        filter_label = QLabel("Filters:")
        filter_label.setMinimumWidth(60)
        self._filter_layout.addWidget(filter_label)

        # Create checkboxes dynamically from config tags
        tags = ConfigManager.load_tags()
        for tag in tags:
            if tag.enabled:
                checkbox = QCheckBox(tag.name)
                checkbox.setChecked(False)  # Default: all filters unchecked (show all)
                checkbox.stateChanged.connect(self._on_filter_changed)
                self._filter_checkboxes[tag.name] = checkbox
                self._filter_layout.addWidget(checkbox, 0)  # No stretch

                # Add a label for count (initially hidden)
                count_label = QLabel("")
                count_label.setStyleSheet("QLabel { color: #90EE90; padding: 0px; margin: 0px; }")  # Light green, no padding/margin
                count_label.setContentsMargins(0, 0, 0, 0)
                count_label.setVisible(False)
                self._filter_count_labels[tag.name] = count_label
                self._filter_layout.addWidget(count_label, 0)  # No stretch

                # Add small spacer between checkbox+count groups (since layout spacing is 0)
                spacer = QLabel("  ")  # Two spaces for separation
                self._filter_layout.addWidget(spacer)

        self._filter_layout.addStretch()

    def _rebuild_filter_ui(self):
        """Rebuild the filter UI after tags have been modified."""
        # Clear existing widgets from layout
        while self._filter_layout.count():
            item = self._filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear the dictionaries
        self._filter_checkboxes.clear()
        self._filter_count_labels.clear()

        # Rebuild the UI
        self._build_filter_ui()

        # Update counts for the new filters
        self._update_tag_counts()

    def _on_open_clicked(self):
        """Handle Open button click - opens file dialog."""
        # Get the last used directory
        last_directory = ConfigManager.load_last_directory()
        if not last_directory:
            last_directory = str(Path.cwd())

        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Log File",
            last_directory,
            "Log Files (*.log);;All Files (*.*)"
        )

        # User cancelled
        if not file_path:
            return

        # Update the file input field (still needed for reload functionality)
        self._file_input.setText(file_path)

        # Remove old file from watcher (if any)
        if self._current_file_path:
            self._file_watcher.removePath(self._current_file_path)

        # Add new file to watcher
        self._current_file_path = file_path
        self._file_watcher.addPath(file_path)

        # Clear file change notification (opening new file)
        self._clear_file_change_notification()

        # Clear existing entries
        with self._entries_lock:
            self._log_entries.clear()

        self._log_model.clear()
        self._update_entry_count(0, 0)

        # Save file path to config
        ConfigManager.save_last_file_path(file_path)

        # Update status bar file
        self._update_file_status(file_path)

        # Start async parsing
        self._update_status("Starting parse...")
        self._parser.parse_async(file_path, self._parser_callback)

        # Switch focus to search input for convenience
        self._search_input.setFocus()

    def _auto_load_last_file(self, file_path: str):
        """
        Auto-load the last opened file on startup.

        Args:
            file_path: Path to the file to load
        """
        # Add to file watcher
        self._current_file_path = file_path
        self._file_watcher.addPath(file_path)

        # Update status bar file
        self._update_file_status(file_path)

        # Start async parsing
        self._update_status("Loading last file...")
        self._parser.parse_async(file_path, self._parser_callback)

        # Switch focus to search input
        self._search_input.setFocus()

    def _on_reload_clicked(self):
        """Handle Reload action (Ctrl+R)."""
        file_path = self._file_input.text().strip()

        if not file_path:
            self._update_status("Error: No file to reload")
            return

        # Check if file exists
        if not Path(file_path).exists():
            self._update_status(f"Error: File not found: {file_path}")
            return

        # Clear existing entries
        with self._entries_lock:
            self._log_entries.clear()

        self._log_model.clear()
        self._update_entry_count(0, 0)

        # Clear file change notification (if any)
        self._clear_file_change_notification()

        # Start async parsing (no need to save config, already saved)
        self._update_status("Reloading...")
        self._parser.parse_async(file_path, self._parser_callback)

        print(f"[RELOAD] Reloading file: {file_path}")

        # Switch focus to search input
        self._search_input.setFocus()

    def _on_file_changed(self, path: str):
        """
        Handle file change notification from QFileSystemWatcher.

        Args:
            path: Path to the file that changed
        """
        # Check if file still exists (might have been deleted)
        if not Path(path).exists():
            print(f"[FILE WATCHER] File deleted or moved: {path}")
            # QFileSystemWatcher automatically removes deleted files from watch list
            # No need to show notification for deleted files
            return

        # Show red notification in status bar
        self._show_file_change_notification()
        print(f"[FILE WATCHER] File changed: {path}")

        # Note: QFileSystemWatcher may stop watching after some editors save files
        # (they delete and recreate). Re-add to watcher if needed.
        if path not in self._file_watcher.files():
            self._file_watcher.addPath(path)
            print(f"[FILE WATCHER] Re-added file to watch: {path}")

    def _show_file_change_notification(self):
        """Show red notification that file has been modified."""
        self._status_message.setText("File has been modified - Press Ctrl+R to reload")
        self._status_message.setStyleSheet("QLabel { color: #FF0000; font-weight: bold; }")  # Red text

    def _clear_file_change_notification(self):
        """Clear the file change notification."""
        self._status_message.setStyleSheet("")  # Reset to normal style

    def _setup_statusbar(self):
        """Create and setup the status bar."""
        statusbar = self.statusBar()

        # Qt best practice: Use margins for breathing room, separators for visual clarity
        statusbar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid palette(mid);
            }
            QStatusBar::item {
                border: none;
            }
        """)
        statusbar.setContentsMargins(5, 2, 5, 2)

        # Left side: Status message (stretches to fill available space)
        self._status_message = QLabel("Ready")
        self._status_message.setStyleSheet("QLabel { color: #90EE90; }")  # Light green for normal status
        self._status_message.setMinimumWidth(150)
        self._status_message.setContentsMargins(5, 0, 10, 0)
        statusbar.addWidget(self._status_message, 1)  # stretch=1

        # Separator frame
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        statusbar.addPermanentWidget(separator1)

        # Center-left: Active file (permanent widget)
        self._status_file = QLabel("File: No file loaded")
        self._status_file.setMinimumWidth(220)
        self._status_file.setContentsMargins(10, 0, 10, 0)
        statusbar.addPermanentWidget(self._status_file)

        # Separator frame
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        statusbar.addPermanentWidget(separator2)

        # Center-right: Entry count (permanent widget)
        self._status_entries = QLabel("Entries: 0")
        self._status_entries.setMinimumWidth(150)
        self._status_entries.setContentsMargins(10, 0, 10, 0)
        statusbar.addPermanentWidget(self._status_entries)

        # Right: Line info (permanent widget, initially hidden)
        self._status_line = QLabel("")
        self._status_line.setMinimumWidth(100)
        self._status_line.setContentsMargins(10, 0, 5, 0)
        statusbar.addPermanentWidget(self._status_line)

    def _setup_menubar(self):
        """Create and setup the menubar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        # File -> Open
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open a log file")
        open_action.triggered.connect(self._on_open_clicked)
        file_menu.addAction(open_action)

        # File -> Reload
        reload_action = QAction("&Reload", self)
        reload_action.setShortcut(QKeySequence("Ctrl+R"))
        reload_action.setStatusTip("Reload the current log file")
        reload_action.triggered.connect(self._on_reload_clicked)
        file_menu.addAction(reload_action)

        file_menu.addSeparator()

        # File -> Recent Files (submenu)
        self._recent_files_menu = file_menu.addMenu("Recent &Files")
        self._recent_files_menu.aboutToShow.connect(self._update_recent_files_menu)

        file_menu.addSeparator()

        # File -> Quit
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setStatusTip("Exit the application")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        # Help -> Tag Editor
        tag_editor_action = QAction("&Tag Editor", self)
        tag_editor_action.setStatusTip("Customize log level tags and colors")
        tag_editor_action.triggered.connect(self._show_tag_editor)
        help_menu.addAction(tag_editor_action)

        # Help -> Shortcuts
        shortcuts_action = QAction("&Shortcuts", self)
        shortcuts_action.setStatusTip("Show keyboard and mouse shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts_help)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        # Help -> About
        about_action = QAction("&About LogReader", self)
        about_action.setStatusTip("About LogReader")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts that aren't already in menu actions."""
        # Note: Ctrl+O, Ctrl+R, Ctrl+Q are already set in menu actions

        # Ctrl+C: Copy selected rows
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self._copy_selected_rows)

        # Ctrl+M: Show message details for selected row
        detail_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        detail_shortcut.activated.connect(self._show_message_details)

        # Esc: Clear search
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self._clear_search)

    def _copy_selected_rows(self):
        """Copy selected table rows to clipboard."""
        from PyQt6.QtWidgets import QApplication

        # Get selected rows
        selection_model = self._log_table.selectionModel()
        if not selection_model.hasSelection():
            self._update_status("No rows selected")
            return

        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            self._update_status("No rows selected")
            return

        # Build clipboard text
        clipboard_lines = []
        for index in sorted(selected_rows, key=lambda x: x.row()):
            row = index.row()
            entry = self._log_model.get_entry(row)
            if entry:
                clipboard_lines.append(entry.to_clipboard_format())

        if clipboard_lines:
            clipboard_text = "\n".join(clipboard_lines)
            QApplication.clipboard().setText(clipboard_text)
            self._update_status(f"Copied {len(clipboard_lines)} entries to clipboard")
            print(f"[CLIPBOARD] Copied {len(clipboard_lines)} entries")
        else:
            self._update_status("No entries to copy")

    def _clear_search(self):
        """Clear the search input."""
        self._search_input.clear()
        self._search_input.setFocus()

    def _show_message_details(self):
        """Show detailed message view for currently selected row."""
        from python.message_detail_dialog import MessageDetailDialog

        # Get selected row
        selection_model = self._log_table.selectionModel()
        if not selection_model.hasSelection():
            self._update_status("No row selected - Select a row and press Ctrl+M")
            return

        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            self._update_status("No row selected - Select a row and press Ctrl+M")
            return

        # Get the first selected row (if multiple are selected)
        row = selected_rows[0].row()
        entry = self._log_model.get_entry(row)

        if entry is None:
            self._update_status("Error: Could not get log entry")
            return

        # Show detail dialog
        dialog = MessageDetailDialog(entry, self)
        dialog.exec()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        # Apply combined filters and search
        self._apply_filters()

    def _on_filter_changed(self, state: int):
        """Handle filter checkbox state change."""
        # Apply combined filters and search
        self._apply_filters()

    def _on_file_filter_changed(self, file_name: str):
        """Handle file filter dropdown selection change."""
        # Apply combined filters and search
        self._apply_filters()

    def _apply_filters(self):
        """
        Apply level filters, file filter, and search to log entries.

        This method filters the log entries based on:
        1. Level filters (checkboxes) - OR logic
        2. File filter (dropdown) - AND logic
        3. Search text (substring match) - AND logic with filters

        Updates the table model with filtered indices for efficient display.
        """
        # Get current search term
        search_term = self._search_input.text().strip().lower()

        # Get file filter selection
        selected_file = self._file_filter_combo.currentText() if self._file_filter_combo else "All"
        file_filter_active = (selected_file != "All")

        # Get which tag filters are active (by tag name)
        active_filters = set()
        for tag_name, checkbox in self._filter_checkboxes.items():
            if checkbox.isChecked():
                active_filters.add(tag_name)

        # Check if any filters are active
        # If no filters checked, show all entries
        any_filter_active = len(active_filters) > 0

        # Filter entries
        filtered_indices = []

        # Thread-safe access to entries
        with self._entries_lock:
            for i, entry in enumerate(self._log_entries):
                # Apply level filter (OR logic) - compare by tag name
                if any_filter_active:
                    if entry.level.value not in active_filters:
                        continue  # Skip this entry

                # Apply file filter (AND logic - must also pass level filter)
                if file_filter_active:
                    if entry.source_file != selected_file:
                        continue  # Skip this entry

                # Apply search filter (AND logic - must also pass level filter and file filter)
                if search_term:
                    if search_term not in entry.message.lower():
                        continue  # Skip this entry

                # Entry passed all filters
                filtered_indices.append(i)

        # Update table model with filtered indices
        self._log_model.set_filtered_indices(filtered_indices)

        # Update entry count display
        total = len(self._log_entries)
        shown = len(filtered_indices)
        self._update_entry_count(shown, total)

        # Log filter status
        filter_desc = []
        if active_filters:
            # active_filters now contains tag name strings (not LogLevel objects)
            filter_desc.append(f"Levels: {', '.join(active_filters)}")
        if file_filter_active:
            filter_desc.append(f"File: '{selected_file}'")
        if search_term:
            filter_desc.append(f"Search: '{search_term}'")

        if filter_desc:
            print(f"[FILTER] {' | '.join(filter_desc)} => {shown}/{total} entries")

        # Update tag counts in filter checkboxes
        self._update_tag_counts()

    def _populate_file_filter(self):
        """Populate the file filter dropdown with unique source files from loaded entries."""
        if not self._file_filter_combo:
            return

        # Get current selection to restore after repopulation
        current_selection = self._file_filter_combo.currentText()

        # Clear and reset dropdown
        self._file_filter_combo.blockSignals(True)  # Prevent triggering filter while populating
        self._file_filter_combo.clear()
        self._file_filter_combo.addItem("All")

        # Extract unique file names from entries
        unique_files = set()
        with self._entries_lock:
            for entry in self._log_entries:
                if entry.source_file:
                    unique_files.add(entry.source_file)

        # Add files alphabetically sorted
        for file_name in sorted(unique_files):
            self._file_filter_combo.addItem(file_name)

        # Restore previous selection if it still exists, otherwise select "All"
        index = self._file_filter_combo.findText(current_selection)
        if index >= 0:
            self._file_filter_combo.setCurrentIndex(index)
        else:
            self._file_filter_combo.setCurrentIndex(0)  # "All"

        self._file_filter_combo.blockSignals(False)

        print(f"[FILE FILTER] Populated with {len(unique_files)} files")

    def _update_tag_counts(self):
        """
        Update tag counts in filter checkboxes.

        Counts entries by tag, respecting current search filter (not level filters).
        Only displays counts for tags with show_count=True.
        """
        # Get current search term
        search_term = self._search_input.text().strip().lower()

        # Count entries by tag (respecting current search filter)
        tag_counts: Dict[str, int] = {}

        with self._entries_lock:
            for entry in self._log_entries:
                # Apply search filter if active
                if search_term:
                    if search_term not in entry.message.lower():
                        continue

                # Increment count for this tag
                tag_name = entry.level.value
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

        # Update checkbox labels and count labels (conditionally show counts)
        for tag_name, checkbox in self._filter_checkboxes.items():
            count = tag_counts.get(tag_name, 0)

            # Check if this tag should show count
            tag = ConfigManager.get_or_create_tag(tag_name)
            count_label = self._filter_count_labels.get(tag_name)

            if tag.show_count and count_label:
                # Show count in separate light green label
                count_label.setText(f"[{count}]")
                count_label.setVisible(True)
            elif count_label:
                # Hide count label
                count_label.setVisible(False)

    def _on_jump_clicked(self):
        """Handle Jump to Line button click or Enter key."""
        line_text = self._jump_input.text().strip()

        if not line_text:
            self._update_status("Error: Enter a line number")
            return

        try:
            line_number = int(line_text)
        except ValueError:
            self._update_status(f"Error: Invalid line number '{line_text}'")
            return

        if line_number <= 0:
            self._update_status("Error: Line number must be positive")
            return

        # Search for the entry with this line number
        found_index = None
        with self._entries_lock:
            for i, entry in enumerate(self._log_entries):
                if entry.line_number == line_number:
                    found_index = i
                    break

        if found_index is None:
            self._update_status(f"Error: Line {line_number} not found")
            return

        # Clear all filters to ensure the line is visible
        self._clear_all_filters()

        # Select and scroll to the row
        model_index = self._log_model.index(found_index, 0)
        self._log_table.selectRow(found_index)
        self._log_table.scrollTo(model_index, QTableView.ScrollHint.PositionAtCenter)

        self._update_status(f"Jumped to line {line_number}")
        print(f"[JUMP] Jumped to line {line_number}")

        # Clear the jump input
        self._jump_input.clear()

    def _on_table_double_click(self, index):
        """
        Handle double-click on log table.

        Clears all filters and search, then navigates to the line number
        of the double-clicked entry to show surrounding context.

        Args:
            index: QModelIndex of the clicked cell
        """
        if not index.isValid():
            return

        # Get the entry for this row
        row = index.row()
        entry = self._log_model.get_entry(row)
        if entry is None:
            return

        line_number = entry.line_number

        # Clear all filters and search
        self._clear_all_filters()

        # Find the entry with this line number in the now-unfiltered list
        # and scroll to it
        with self._entries_lock:
            for i, e in enumerate(self._log_entries):
                if e.line_number == line_number:
                    # Select and scroll to this row
                    self._log_table.selectRow(i)
                    model_index = self._log_model.index(i, 0)
                    self._log_table.scrollTo(model_index, QTableView.ScrollHint.PositionAtCenter)

                    self._update_status(f"Cleared filters, showing context for line {line_number}")
                    print(f"[DOUBLE-CLICK] Cleared filters, jumped to line {line_number}")
                    break

    def _clear_all_filters(self):
        """Clear all filters and search to show all entries."""
        # Uncheck all filter checkboxes
        for checkbox in self._filter_checkboxes.values():
            checkbox.setChecked(False)

        # Clear search input
        self._search_input.clear()

        # Reapply filters (which will show all entries)
        self._apply_filters()

    def _update_status(self, message: str):
        """
        Update the status message in status bar.

        Args:
            message: Status message to display
        """
        # Check if this is an error message
        if message.startswith("Error:"):
            # Error messages in red
            self._status_message.setStyleSheet("QLabel { color: #FF0000; font-weight: bold; }")  # Red
        else:
            # Normal status in light green
            self._status_message.setStyleSheet("QLabel { color: #90EE90; }")  # Light green

        self._status_message.setText(message)
        print(f"[STATUS] {message}")

    def _update_entry_count(self, shown: int, total: int):
        """
        Update the entry count in status bar.

        Args:
            shown: Number of entries currently shown
            total: Total number of entries
        """
        if shown == total:
            self._status_entries.setText(f"Entries: {total:,}")
        else:
            self._status_entries.setText(f"Entries: {total:,} ({shown:,} visible)")

    def _update_file_status(self, file_path: str):
        """
        Update the active file in status bar.

        Args:
            file_path: Path to the active log file
        """
        if file_path:
            # Show just the filename, not full path
            filename = Path(file_path).name
            self._status_file.setText(f"File: {filename}")
        else:
            self._status_file.setText("File: No file loaded")

    def _parser_callback(self, status: str, entries: List[LogEntry]):
        """
        Callback from parser thread with progress updates.

        This runs in the parser thread, so we emit a signal to marshal
        the call to the main UI thread.

        Args:
            status: Status message from parser
            entries: Current list of parsed entries
        """
        # Make a copy of entries to avoid threading issues
        entries_copy = entries.copy()

        # Emit signal to update UI (thread-safe)
        self._parser_signals.progress_update.emit(status, entries_copy)

    def _on_parser_progress(self, status: str, entries: List[LogEntry]):
        """
        Handle parser progress update in the UI thread.

        This is called via Qt signal, so it runs in the main thread.

        Args:
            status: Status message from parser
            entries: Current list of parsed entries
        """
        # Update status message
        self._update_status(status)

        # Update stored entries (thread-safe)
        with self._entries_lock:
            self._log_entries = entries

        # Update table model
        self._log_model.set_entries(entries)

        # Populate file filter dropdown when parsing completes
        if status.startswith("Complete:"):
            self._populate_file_filter()

        # Apply any active filters
        self._apply_filters()

        # Update status with completion message
        if status.startswith("Complete:"):
            self._update_status(status)

        print(f"[PARSER] {status}")

    def _update_recent_files_menu(self):
        """Update the Recent Files submenu with current recent files."""
        # Clear existing menu items
        self._recent_files_menu.clear()

        # Get recent files
        recent_files = ConfigManager.get_recent_files()

        if not recent_files:
            # Show "No Recent Files" if list is empty
            no_files_action = QAction("No Recent Files", self)
            no_files_action.setEnabled(False)
            self._recent_files_menu.addAction(no_files_action)
            return

        # Add each recent file
        for file_path in recent_files:
            # Create shortened display name
            display_name = Path(file_path).name
            action = QAction(display_name, self)
            action.setStatusTip(file_path)

            # Add checkmark if this is the currently open file
            if file_path == self._current_file_path:
                action.setCheckable(True)
                action.setChecked(True)

            # Connect to open handler
            action.triggered.connect(lambda checked=False, path=file_path: self._open_recent_file(path))
            self._recent_files_menu.addAction(action)

        # Add separator and Clear option
        self._recent_files_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self._recent_files_menu.addAction(clear_action)

    def _open_recent_file(self, file_path: str):
        """
        Open a file from the recent files list.

        Args:
            file_path: Path to the file to open
        """
        # Check if file still exists
        if not Path(file_path).exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"File no longer exists:\n{file_path}"
            )
            return

        # Simulate clicking Open with this file
        self._file_input.setText(file_path)

        # Remove old file from watcher
        if self._current_file_path:
            self._file_watcher.removePath(self._current_file_path)

        # Add new file to watcher
        self._current_file_path = file_path
        self._file_watcher.addPath(file_path)

        # Clear file change notification
        self._clear_file_change_notification()

        # Clear existing entries
        with self._entries_lock:
            self._log_entries.clear()

        self._log_model.clear()
        self._update_entry_count(0, 0)

        # Save file path to config (updates recent files)
        ConfigManager.save_last_file_path(file_path)

        # Update status bar file
        self._update_file_status(file_path)

        # Start async parsing
        self._update_status("Starting parse...")
        self._parser.parse_async(file_path, self._parser_callback)

        # Switch focus to search input
        self._search_input.setFocus()

    def _clear_recent_files(self):
        """Clear the recent files list."""
        reply = QMessageBox.question(
            self,
            "Clear Recent Files",
            "Are you sure you want to clear the recent files list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            ConfigManager.clear_recent_files()
            self._update_status("Recent files cleared")

    def _show_tag_editor(self):
        """Show Tag Editor dialog."""
        from python.tag_editor_dialog import TagEditorDialog

        dialog = TagEditorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save updated tags to config
            updated_tags = dialog.get_tags()
            ConfigManager.save_tags(updated_tags)

            # Rebuild filter UI to reflect changes (enabled/disabled tags, show_count, etc.)
            self._rebuild_filter_ui()

            # Update status bar
            self._update_status("Tags updated!")

    def _show_shortcuts_help(self):
        """Show Shortcuts help dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Shortcuts")
        msg.setTextFormat(Qt.TextFormat.RichText)

        help_text = """
        <h3>Keyboard Shortcuts</h3>
        <table cellpadding="5">
        <tr><td><b>Ctrl+O</b></td><td>Open log file</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Reload current log file</td></tr>
        <tr><td><b>Ctrl+C</b></td><td>Copy selected rows to clipboard</td></tr>
        <tr><td><b>Ctrl+M</b></td><td>Show full message details for selected row</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select all visible rows</td></tr>
        <tr><td><b>Esc</b></td><td>Clear search input</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit application</td></tr>
        </table>

        <h3>Mouse Actions</h3>
        <table cellpadding="5">
        <tr><td><b>Click</b></td><td>Select single row</td></tr>
        <tr><td><b>Ctrl+Click</b></td><td>Add/remove row from selection</td></tr>
        <tr><td><b>Shift+Click</b></td><td>Select range of rows</td></tr>
        <tr><td><b>Double-Click</b></td><td>Clear filters/search and show context around clicked line</td></tr>
        <tr><td><b>Hover</b></td><td>Show full message text as tooltip (Message column only)</td></tr>
        </table>

        <p><i>Tip: Hover over long messages to see the full text, or press Ctrl+M for a detailed view with copy functionality!</i></p>
        """

        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _show_about_dialog(self):
        """Show About LogReader dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle("About LogReader")
        msg.setTextFormat(Qt.TextFormat.RichText)

        about_text = """
        <h2>LogReader</h2>
        <p><b>Version:</b> 1.1</p>
        <p><b>License:</b> MIT License</p>

        <p>A modern, professional GUI log viewer built with Python and PyQt6.</p>

        <h3>Features</h3>
        <ul>
        <li>Native file dialog with directory memory</li>
        <li>Line numbers and jump to line navigation</li>
        <li>Real-time filtering and instant search</li>
        <li>Async parsing with progress updates</li>
        <li>Color-coded log levels</li>
        <li>Multi-row selection and copy</li>
        </ul>

        <h3>Technology</h3>
        <p><b>Built with:</b> Python 3.10+ and PyQt6</p>

        <h3>Copyright</h3>
        <p>© 2025 Dave Packer</p>
        <p>This software is provided under the MIT License.</p>

        <p><i>For documentation, visit the project repository or see USER_GUIDE.md</i></p>
        """

        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def closeEvent(self, event):
        """
        Handle window close event.

        Stop any active parsing before closing.

        Args:
            event: QCloseEvent
        """
        # Stop parser if running
        if self._parser.is_parsing():
            print("[INFO] Stopping parser before exit...")
            self._parser.stop_parsing()

        # Accept the close event
        event.accept()
