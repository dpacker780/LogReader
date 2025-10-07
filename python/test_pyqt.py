"""
Simple PyQt6 test to verify installation.
This script creates a basic window to confirm PyQt6 is working.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt


def main():
    """Create and show a simple test window."""
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("PyQt6 Installation Test")
    window.setGeometry(100, 100, 400, 200)

    # Create label
    label = QLabel("PyQt6 is installed and working!", window)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)

    # Show window
    window.show()

    print("[OK] PyQt6 installation verified!")
    print("[OK] Window opened successfully")
    print("Close the window to continue...")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
