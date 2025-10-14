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
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QFileSystemWatcher, QTimer, QStorageInfo
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut, QAction

from python.log_entry import LogLevel, LogEntry
from python.log_table_model import LogTableModel
from python.log_parser import LogParser
from python.config import ConfigManager
from python.live_log_monitor import LiveLogMonitor, ChangeType


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

        # Live log monitoring
        self._live_monitor = LiveLogMonitor()

        # Polling timer (backup for file watching on network drives)
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._on_poll_timer)
        self._poll_timer.setInterval(2000)  # Poll every 2 seconds

        # Debounce timer for file changes (prevents rapid update spam)
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)  # Fire only once
        self._debounce_timer.timeout.connect(self._process_pending_file_change)
        self._pending_file_change_path: str = ""

        # Parser and signals
        self._parser = LogParser()
        self._parser_signals = ParserSignals()
        self._parser_signals.progress_update.connect(self._on_parser_progress)
        self._parser_signals_append = ParserSignals()
        self._parser_signals_append.progress_update.connect(self._on_parser_append_progress)

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

        # Search navigation state (v1.3 - navigation instead of filtering)
        self._search_result_indices: List[int] = []  # Indices into filtered view
        self._current_search_index: int = -1  # Current position in search results
        self._search_prev_button: QPushButton = None
        self._search_next_button: QPushButton = None
        self._search_counter_label: QLabel = None

        # Status bar widgets
        self._status_message: QLabel = None
        self._status_file: QLabel = None
        self._status_entries: QLabel = None
        self._status_line: QLabel = None
        self._status_live_indicator: QLabel = None

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

    def _is_network_drive(self, file_path: str) -> bool:
        """
        Check if file is on a network drive using Qt's QStorageInfo (cross-platform).

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is on a network drive, False otherwise
        """
        try:
            storage = QStorageInfo(file_path)
            if not storage.isValid():
                return False  # Assume local if detection fails

            # Get device and filesystem type as bytes, then decode
            device_bytes = storage.device()
            device = device_bytes.data().decode('utf-8', errors='ignore') if device_bytes else ""

            fstype_bytes = storage.fileSystemType()
            fs_type = fstype_bytes.data().decode('utf-8', errors='ignore') if fstype_bytes else ""

            if sys.platform == 'win32':
                # On Windows, local drives start with \\?\Volume
                # Network drives have different patterns (UNC paths, mapped drives)
                is_network = not device.startswith('\\\\?\\Volume')
                return is_network
            else:
                # On Linux/macOS, check for network filesystem types
                network_fs_types = ['nfs', 'nfs4', 'cifs', 'smb', 'smbfs', 'fuse.sshfs']
                return fs_type.lower() in network_fs_types
        except Exception as e:
            print(f"[NETWORK CHECK] Detection failed: {e} - assuming local")
            return False  # Assume local if detection fails

    def _get_search_highlight_colors(self):
        """
        Get appropriate highlight colors based on current theme.

        Returns:
            Tuple of (all_matches_color, current_match_color) as hex strings
        """
        palette = self.palette()
        base_color = palette.color(palette.ColorRole.Base)
        is_dark = base_color.lightness() < 128

        if is_dark:
            # Dark theme: dark blue tints (more saturated for visibility)
            return "#2A4A6A", "#3A5A8A"
        else:
            # Light theme: light blue tints (softer for light backgrounds)
            return "#D0E8FF", "#B0D0FF"

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

        v1.3: Reorganized into two side-by-side sections:
        - Section 1 (Left): Search & Navigation
        - Section 2 (Right): Filters & Controls

        Returns:
            QFrame containing search input and level filter checkboxes
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setMaximumHeight(120)  # Increased by 20 pixels for more breathing room

        # Main horizontal layout for side-by-side sections
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)  # Space before separator

        # === SECTION 1: SEARCH & NAVIGATION ===
        search_section = QFrame()
        # No frame style - clean look
        search_section_layout = QVBoxLayout(search_section)
        search_section_layout.setContentsMargins(5, 5, 5, 5)
        search_section_layout.setSpacing(3)

        # Row 1: Search input
        search_input_row = QHBoxLayout()
        search_label = QLabel("Search:")
        search_input_row.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("search term")
        self._search_input.setMaxLength(50)
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_input.returnPressed.connect(self._on_search_changed)

        # Add search button inside QLineEdit
        search_action = QAction("🔍", self._search_input)
        search_action.setToolTip("Execute search (or press Enter)")
        search_action.triggered.connect(self._on_search_changed)
        self._search_input.addAction(search_action, QLineEdit.ActionPosition.TrailingPosition)

        search_input_row.addWidget(self._search_input, stretch=1)
        search_section_layout.addLayout(search_input_row)

        # Row 2: Navigation controls (directly below search)
        nav_row = QHBoxLayout()

        # Previous button
        self._search_prev_button = QPushButton("◀ Prev")
        self._search_prev_button.setMaximumWidth(70)
        self._search_prev_button.setEnabled(False)
        self._search_prev_button.setToolTip("Previous search result (Ctrl+P)")
        self._search_prev_button.clicked.connect(self._on_search_prev)
        nav_row.addWidget(self._search_prev_button)

        # Next button
        self._search_next_button = QPushButton("Next ▶")
        self._search_next_button.setMaximumWidth(70)
        self._search_next_button.setEnabled(False)
        self._search_next_button.setToolTip("Next search result (Ctrl+N)")
        self._search_next_button.clicked.connect(self._on_search_next)
        nav_row.addWidget(self._search_next_button)

        # Result counter
        self._search_counter_label = QLabel("")
        self._search_counter_label.setMinimumWidth(100)
        self._search_counter_label.setStyleSheet("QLabel { color: #90EE90; }")
        nav_row.addWidget(self._search_counter_label)

        nav_row.addStretch()  # Push everything to the left
        search_section_layout.addLayout(nav_row)

        # Add Section 1 to main layout (compact width)
        search_section.setMinimumWidth(250)
        search_section.setMaximumWidth(300)
        layout.addWidget(search_section, stretch=0)  # No stretch - keep compact

        # Add vertical separator between sections
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # === SECTION 2: FILTERS & CONTROLS ===
        filter_section = QFrame()
        # No frame style - clean look
        filter_section_layout = QVBoxLayout(filter_section)
        filter_section_layout.setContentsMargins(5, 5, 5, 5)
        filter_section_layout.setSpacing(3)

        # Row 1: File filter, Jump to Line, Reset All
        controls_row = QHBoxLayout()

        # File filter dropdown
        file_label = QLabel("File:")
        controls_row.addWidget(file_label)

        self._file_filter_combo = QComboBox()
        self._file_filter_combo.setFixedWidth(250)
        self._file_filter_combo.addItem("All")
        self._file_filter_combo.currentTextChanged.connect(self._on_file_filter_changed)
        controls_row.addWidget(self._file_filter_combo)

        controls_row.addSpacing(20)

        # Jump to Line controls
        jump_label = QLabel("Jump to Line:")
        controls_row.addWidget(jump_label)

        self._jump_input = QLineEdit()
        self._jump_input.setPlaceholderText("#")
        self._jump_input.setMaximumWidth(80)
        self._jump_input.returnPressed.connect(self._on_jump_clicked)
        controls_row.addWidget(self._jump_input)

        self._jump_button = QPushButton("Go")
        self._jump_button.setMaximumWidth(50)
        self._jump_button.clicked.connect(self._on_jump_clicked)
        controls_row.addWidget(self._jump_button)

        controls_row.addStretch()

        # Reset All button
        reset_button = QPushButton("Reset All")
        reset_button.setMaximumWidth(80)
        reset_button.setToolTip("Clear all filters, search, and jump to line")
        reset_button.clicked.connect(self._on_reset_all_clicked)
        controls_row.addWidget(reset_button)

        filter_section_layout.addLayout(controls_row)

        # Row 2: Filter checkboxes
        self._filter_layout = QHBoxLayout()
        self._filter_layout.setSpacing(0)
        self._build_filter_ui()
        filter_section_layout.addLayout(self._filter_layout)

        # Add Section 2 to main layout (side-by-side, stretches to fill remaining space)
        layout.addWidget(filter_section, stretch=1)

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

        # Add stretch to fill remaining space (Reset All button moved to navigation section)
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

        Uses debouncing to prevent rapid-fire updates from freezing the UI.

        Args:
            path: Path to the file that changed
        """
        # Check if file still exists (might have been deleted)
        if not Path(path).exists():
            print(f"[FILE WATCHER] File deleted or moved: {path}")
            # QFileSystemWatcher automatically removes deleted files from watch list
            # No need to show notification for deleted files
            return

        # Note: QFileSystemWatcher may stop watching after some editors save files
        # (they delete and recreate). Re-add to watcher if needed.
        if path not in self._file_watcher.files():
            self._file_watcher.addPath(path)
            print(f"[FILE WATCHER] Re-added file to watch: {path}")

        # If live mode is disabled, just show notification
        if not self._live_monitor.is_live_mode():
            self._show_file_change_notification()
            return

        # Check if parser is already running (prevent overlapping parses)
        if self._parser.is_parsing():
            return  # Silently ignore if parser is busy

        # Debounce: Store the path and start/restart timer
        # This delays processing until 1 second after the last change
        self._pending_file_change_path = path
        self._debounce_timer.stop()  # Cancel any pending timer
        self._debounce_timer.start(1000)  # Wait 1 second (1000ms)

    def _process_pending_file_change(self):
        """
        Process a pending file change after debounce timer expires.

        This is called 1 second after the last file change notification,
        preventing rapid-fire updates from freezing the UI.
        """
        path = self._pending_file_change_path
        if not path:
            return

        # Double-check file still exists
        if not Path(path).exists():
            print(f"[FILE WATCHER] File no longer exists: {path}")
            return

        # Detect change type
        change_type = self._live_monitor.detect_change_type(path)

        if change_type == ChangeType.NO_CHANGE:
            # Spurious notification - silently ignore
            return

        elif change_type == ChangeType.NEW_FILE:
            print(f"[DEBOUNCE] New file detected - performing full reload")
            self._update_status("🔄 File replaced - reloading...")
            # Full reload (existing behavior)
            self._on_reload_clicked()

        elif change_type == ChangeType.APPEND:
            print(f"[DEBOUNCE] Append detected - parsing new entries")
            self._update_status("🔄 Loading new entries...")

            # Parse only appended content
            start_pos = self._live_monitor.get_append_start_position()
            start_line = self._live_monitor.get_next_line_number()

            # Use async append parsing
            def append_callback(status: str, new_entries: List[LogEntry]):
                # Make a copy for thread safety
                entries_copy = new_entries.copy()
                # Emit signal to UI thread
                self._parser_signals_append.progress_update.emit(status, entries_copy)

            self._parser.parse_append_async(path, start_pos, start_line, append_callback)

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

        # Separator frame
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.VLine)
        separator3.setFrameShadow(QFrame.Shadow.Sunken)
        statusbar.addPermanentWidget(separator3)

        # Live mode indicator (permanent widget)
        self._status_live_indicator = QLabel("⏸ Manual")
        self._status_live_indicator.setMinimumWidth(80)
        self._status_live_indicator.setContentsMargins(10, 0, 10, 0)
        self._status_live_indicator.setStyleSheet("QLabel { color: #808080; }")  # Gray when inactive
        self._status_live_indicator.setToolTip("Live update mode (Options → Live Update Mode)")
        statusbar.addPermanentWidget(self._status_live_indicator)

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

        # Options Menu
        options_menu = menubar.addMenu("&Options")

        # Options -> Live Update Mode
        self._live_mode_action = QAction("&Live Update Mode", self)
        self._live_mode_action.setCheckable(True)
        self._live_mode_action.setChecked(False)
        self._live_mode_action.setStatusTip("Automatically update log view when file changes")
        self._live_mode_action.triggered.connect(self._on_live_mode_toggled)
        options_menu.addAction(self._live_mode_action)

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

        # v1.3: Search navigation shortcuts
        # Ctrl+N: Next search result
        next_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        next_shortcut.activated.connect(self._on_search_next)

        # Ctrl+P: Previous search result
        prev_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        prev_shortcut.activated.connect(self._on_search_prev)

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

    def _on_search_changed(self):
        """Handle search execution (Enter key or search button click)."""
        # Apply combined filters and search
        self._apply_filters()

    def _on_search_text_changed(self, text: str):
        """
        Handle search text change (only triggers when text becomes empty).

        This avoids reintroducing "search while typing" behavior, but allows
        the clear button (X) to immediately update the display.

        Args:
            text: The new text in the search box
        """
        # Only trigger filter update when text becomes empty (clear button clicked)
        if not text.strip():
            self._apply_filters()

    def _on_filter_changed(self, state: int):
        """Handle filter checkbox state change."""
        # Apply combined filters and search
        self._apply_filters()

    def _on_file_filter_changed(self, file_name: str):
        """Handle file filter dropdown selection change."""
        # Update visual styling based on filter state
        self._update_file_filter_style()
        # Apply combined filters and search
        self._apply_filters()

    def _apply_filters(self):
        """
        Apply level filters, file filter, and search to log entries.

        v1.3 Change: Search now performs navigation instead of filtering.
        - Level and file filters still filter entries
        - Search finds matches within filtered entries and highlights them
        - Use Previous/Next buttons or Ctrl+P/Ctrl+N to navigate results

        This method filters the log entries based on:
        1. Level filters (checkboxes) - OR logic
        2. File filter (dropdown) - AND logic
        3. Search text - NAVIGATION (not filtering)

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

        # Filter entries (NOT including search - v1.3 change)
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

                # Entry passed all filters (search NOT applied here)
                filtered_indices.append(i)

        # Update table model with filtered indices
        self._log_model.set_filtered_indices(filtered_indices)

        # Update entry count display
        total = len(self._log_entries)
        shown = len(filtered_indices)
        self._update_entry_count(shown, total)

        # v1.3: Perform search navigation (find matches within filtered view)
        if search_term:
            self._perform_search_navigation(search_term, filtered_indices)
        else:
            # No search term - clear search highlighting
            self._clear_search_navigation()

        # Log filter status
        filter_desc = []
        if active_filters:
            # active_filters now contains tag name strings (not LogLevel objects)
            filter_desc.append(f"Levels: {', '.join(active_filters)}")
        if file_filter_active:
            filter_desc.append(f"File: '{selected_file}'")
        if search_term:
            filter_desc.append(f"Search: '{search_term}' (navigation mode)")

        if filter_desc:
            print(f"[FILTER] {' | '.join(filter_desc)} => {shown}/{total} entries")

        # Update tag counts in filter checkboxes
        self._update_tag_counts()

    def _perform_search_navigation(self, search_term: str, filtered_indices: List[int]):
        """
        Perform search navigation - find matches and highlight them (v1.3).

        Args:
            search_term: Search term (already lowercase)
            filtered_indices: List of indices in the filtered view
        """
        # Find all matching rows in the filtered view
        search_matches = []
        with self._entries_lock:
            for row_index, entry_index in enumerate(filtered_indices):
                if entry_index < len(self._log_entries):
                    entry = self._log_entries[entry_index]
                    if search_term in entry.message.lower():
                        search_matches.append(row_index)

        # Update search state
        self._search_result_indices = search_matches
        match_count = len(search_matches)

        if match_count > 0:
            # Jump to first result
            self._current_search_index = 0
            current_row = search_matches[0]

            # Get theme-aware colors (only one color needed now - all matches use same highlight)
            all_color, _ = self._get_search_highlight_colors()

            # Apply highlighting to table model (all matches, no "current" distinction)
            self._log_model.set_search_highlights(
                search_matches,
                -1,  # No special "current" row highlighting
                all_color,
                ""   # No current match color
            )

            # Select and scroll to first result
            self._log_table.selectRow(current_row)
            model_index = self._log_model.index(current_row, 0)
            self._log_table.scrollTo(model_index, QTableView.ScrollHint.PositionAtCenter)

            # Update UI
            self._search_counter_label.setText(f"Result 1 of {match_count}")
            self._search_prev_button.setEnabled(match_count > 1)
            self._search_next_button.setEnabled(match_count > 1)

            # Update status
            self._update_status(f"Found {match_count} matches for '{search_term}'")
            print(f"[SEARCH] Found {match_count} matches, jumped to first result")
        else:
            # No matches found
            self._current_search_index = -1
            self._log_model.clear_search_highlights()
            self._search_counter_label.setText("No results")
            self._search_prev_button.setEnabled(False)
            self._search_next_button.setEnabled(False)
            self._update_status(f"No matches found for '{search_term}'")
            print(f"[SEARCH] No matches found for '{search_term}'")

    def _clear_search_navigation(self):
        """Clear search navigation state and highlighting (v1.3)."""
        self._search_result_indices.clear()
        self._current_search_index = -1
        self._log_model.clear_search_highlights()
        self._search_counter_label.setText("")
        self._search_prev_button.setEnabled(False)
        self._search_next_button.setEnabled(False)

    def _on_search_prev(self):
        """Navigate to previous search result (v1.3)."""
        if not self._search_result_indices or self._current_search_index < 0:
            return

        # Circular navigation: wrap to end if at beginning
        self._current_search_index = (self._current_search_index - 1) % len(self._search_result_indices)
        current_row = self._search_result_indices[self._current_search_index]

        # Select and scroll to result
        self._log_table.selectRow(current_row)
        model_index = self._log_model.index(current_row, 0)
        self._log_table.scrollTo(model_index, QTableView.ScrollHint.PositionAtCenter)

        # Update counter
        self._search_counter_label.setText(
            f"Result {self._current_search_index + 1} of {len(self._search_result_indices)}"
        )

        print(f"[SEARCH] Previous result: {self._current_search_index + 1}/{len(self._search_result_indices)}")

    def _on_search_next(self):
        """Navigate to next search result (v1.3)."""
        if not self._search_result_indices or self._current_search_index < 0:
            return

        # Circular navigation: wrap to beginning if at end
        self._current_search_index = (self._current_search_index + 1) % len(self._search_result_indices)
        current_row = self._search_result_indices[self._current_search_index]

        # Select and scroll to result
        self._log_table.selectRow(current_row)
        model_index = self._log_model.index(current_row, 0)
        self._log_table.scrollTo(model_index, QTableView.ScrollHint.PositionAtCenter)

        # Update counter
        self._search_counter_label.setText(
            f"Result {self._current_search_index + 1} of {len(self._search_result_indices)}"
        )

        print(f"[SEARCH] Next result: {self._current_search_index + 1}/{len(self._search_result_indices)}")

    def _update_file_filter_style(self):
        """Update file filter combo styling based on active state."""
        if not self._file_filter_combo:
            return

        selected_file = self._file_filter_combo.currentText()
        if selected_file != "All":
            # Active filter - use orange text color to indicate filter is active
            # This preserves the native dropdown styling while making it obvious
            self._file_filter_combo.setStyleSheet("""
                QComboBox {
                    color: #FF8800;
                    font-weight: bold;
                }
            """)
        else:
            # Inactive - reset to default
            self._file_filter_combo.setStyleSheet("")

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

        # Update visual styling after repopulation
        self._update_file_filter_style()

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
        Handle double-click on log table (v1.3).

        Shows message detail dialog (equivalent to Ctrl+M).
        This replaces the old behavior of clearing filters.

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

        # Show message details dialog (same as Ctrl+M)
        from python.message_detail_dialog import MessageDetailDialog

        dialog = MessageDetailDialog(entry, self)
        dialog.exec()

        print(f"[DOUBLE-CLICK] Opened message detail dialog for line {entry.line_number}")

    def _clear_all_filters(self):
        """Clear all filters and search to show all entries."""
        # Uncheck all filter checkboxes
        for checkbox in self._filter_checkboxes.values():
            checkbox.setChecked(False)

        # Clear search input
        self._search_input.clear()

        # Reapply filters (which will show all entries)
        self._apply_filters()

    def _on_reset_all_clicked(self):
        """Handle Reset All button click - clears all filters, search, file filter, and jump to line (v1.3)."""
        # Uncheck all level filter checkboxes
        for checkbox in self._filter_checkboxes.values():
            checkbox.setChecked(False)

        # Clear search input
        self._search_input.clear()

        # Reset file filter to "All"
        if self._file_filter_combo:
            self._file_filter_combo.setCurrentIndex(0)  # Set to "All"

        # Clear jump to line input
        if self._jump_input:
            self._jump_input.clear()

        # v1.3: Clear search navigation state
        self._clear_search_navigation()

        # Reapply filters (which will show all entries and clear highlighting)
        self._apply_filters()

        self._update_status("All filters and search cleared")
        print("[RESET ALL] Cleared all filters, search, file filter, jump to line, and search navigation")

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

            # Initialize live monitor state after successful parse
            self._live_monitor.initialize_file_state(
                self._current_file_path,
                len(entries)
            )

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

    def _on_live_mode_toggled(self, checked: bool):
        """
        Handle Live Update Mode toggle from Options menu.

        Args:
            checked: True if live mode was enabled, False if disabled
        """
        self._live_monitor.enable_live_mode(checked)

        if checked:
            self._update_status("🔄 Live update mode enabled")
            print("[LIVE MODE] Enabled - will auto-update on file changes")

            # Only start polling timer for network drives (backup for QFileSystemWatcher)
            if self._current_file_path:
                is_network = self._is_network_drive(self._current_file_path)
                if is_network:
                    self._poll_timer.start()
                    print("[POLL TIMER] Started (2s interval) - Network drive detected")
                else:
                    print("[POLL TIMER] Skipped - Local drive (QFileSystemWatcher sufficient)")
        else:
            self._update_status("Live update mode disabled")
            print("[LIVE MODE] Disabled - manual reload required (Ctrl+R)")
            # Stop polling timer
            self._poll_timer.stop()
            print("[POLL TIMER] Stopped")

        # Update status bar live indicator
        self._update_live_mode_indicator()

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
        <tr><td><b>Ctrl+N</b></td><td>Next search result</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>Previous search result</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select all visible rows</td></tr>
        <tr><td><b>Esc</b></td><td>Clear search input</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit application</td></tr>
        </table>

        <h3>Mouse Actions</h3>
        <table cellpadding="5">
        <tr><td><b>Click</b></td><td>Select single row</td></tr>
        <tr><td><b>Ctrl+Click</b></td><td>Add/remove row from selection</td></tr>
        <tr><td><b>Shift+Click</b></td><td>Select range of rows</td></tr>
        <tr><td><b>Double-Click</b></td><td>Show message details dialog</td></tr>
        <tr><td><b>Hover</b></td><td>Show full message text as tooltip (Message column only)</td></tr>
        </table>

        <p><i>Tip: Use search to find matches, then navigate with Prev/Next buttons or Ctrl+P/Ctrl+N!</i></p>
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
        <p><b>Version:</b> 1.3</p>
        <p><b>License:</b> MIT License</p>

        <p>A modern, professional GUI log viewer built with Python and PyQt6.</p>

        <h3>Features</h3>
        <ul>
        <li>Native file dialog with directory memory</li>
        <li>Line numbers and jump to line navigation</li>
        <li>Real-time filtering with search navigation</li>
        <li>Theme-aware search highlighting</li>
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

    def _update_live_mode_indicator(self):
        """Update the live mode indicator in the status bar."""
        if self._live_monitor.is_live_mode():
            # Show active indicator
            self._status_live_indicator.setText("🔄 Live")
            self._status_live_indicator.setStyleSheet("QLabel { color: #00FF00; font-weight: bold; }")  # Bright green
            self._status_live_indicator.setToolTip("Live update mode ACTIVE - Auto-reloading on file changes")
        else:
            # Show inactive indicator
            self._status_live_indicator.setText("⏸ Manual")
            self._status_live_indicator.setStyleSheet("QLabel { color: #808080; }")  # Gray
            self._status_live_indicator.setToolTip("Live update mode OFF - Use Ctrl+R to reload manually")

    def _on_parser_append_progress(self, status: str, new_entries: List[LogEntry]):
        """
        Handle append parser progress update in the UI thread.

        This is called via Qt signal when new log entries are parsed in append mode.

        Args:
            status: Status message from parser
            new_entries: List of newly parsed entries to append
        """
        # Update status message
        self._update_status(status)

        if not new_entries:
            return

        # Append new entries to existing entries (thread-safe)
        with self._entries_lock:
            self._log_entries.extend(new_entries)
            total_entries = len(self._log_entries)

        # Update table model with all entries
        self._log_model.set_entries(self._log_entries)

        # Apply filters to include new entries
        self._apply_filters()

        # Update file state in live monitor
        if status.startswith("Complete:") or status.startswith("Partial:"):
            stat = Path(self._current_file_path).stat()
            self._live_monitor.update_state(stat.st_size, total_entries, stat.st_mtime)

            # Auto-scroll to bottom if user was already at bottom
            self._auto_scroll_if_at_bottom()

        print(f"[APPEND] {status} - Total entries: {total_entries}")

    def _auto_scroll_if_at_bottom(self):
        """
        Auto-scroll to bottom if user was already scrolled to the bottom.

        This implements smart auto-scroll behavior for live updates.
        """
        # Get scrollbar
        scrollbar = self._log_table.verticalScrollBar()

        # Check if user is near the bottom (within 50 pixels)
        # This allows for some slack in case filtering changed the view
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 50

        if at_bottom:
            # Scroll to the very bottom
            scrollbar.setValue(scrollbar.maximum())
            print("[AUTO-SCROLL] Scrolled to bottom (new entries)")

    def _on_poll_timer(self):
        """
        Polling timer handler (backup for file watching).

        This timer polls the file periodically to catch changes that
        QFileSystemWatcher might miss (e.g., on network drives).
        """
        # Only poll if live mode is active and we have a file loaded
        if not self._live_monitor.is_live_mode() or not self._current_file_path:
            return

        # Check if parser is already running (avoid overlapping parses)
        if self._parser.is_parsing():
            return

        # Simulate a file change event
        # The _on_file_changed handler will detect if there's actually a change
        self._on_file_changed(self._current_file_path)

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
