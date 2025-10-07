"""
LogReader - Python/PyQt6 Version v1.1

Main application entry point.
Cross-platform log file viewer with filtering and search capabilities.

Version: 1.1 - Dynamic Tag System
Date: 2025
Author: LogReader Team
License: MIT
"""

__version__ = "1.1"

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from python.main_window import MainWindow


def main():
    """
    Initialize and run the LogReader application.

    Returns:
        Exit code (0 for success)
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("LogReader")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("LogReader")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
