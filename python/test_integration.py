"""
Integration test - Test full application with real log file.

This script automatically loads a log file to test the complete workflow.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from python.main_window import MainWindow


def main():
    """Run integration test."""
    print("=" * 60)
    print("LogReader Integration Test")
    print("=" * 60)

    app = QApplication(sys.argv)
    app.setApplicationName("LogReader Test")

    # Create main window
    window = MainWindow()

    # Set the file path to a test file
    test_file = "helix.log"
    if not Path(test_file).exists():
        test_file = "test_input.log"

    if Path(test_file).exists():
        # Simulate loading a file
        window._file_input.setText(test_file)

        # Programmatically trigger file open
        def auto_open():
            # Clear entries
            window._log_model.clear()
            window._update_entry_count(0, 0)
            window._update_file_status(test_file)
            window._update_status("Starting parse...")
            window._parser.parse_async(test_file, window._parser_callback)

        # Trigger after 100ms
        QTimer.singleShot(100, auto_open)

        print(f"\n[INFO] Auto-loading file: {test_file}")
        print("[INFO] Use File -> Open or Ctrl+O to open a different file")
        print("[INFO] You should see:")
        print("  - No top file input pane (cleaner UI)")
        print("  - Status bar at bottom")
        print("  - Progress updates in status bar")
        print("  - Log entries appear in table with colors")
    else:
        print("\n[WARNING] No test log files found")
        print("[INFO] Use File -> Open or press Ctrl+O to open a log file")

    window.show()

    print("\n[OK] Window opened")
    print("Close the window to exit...")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
