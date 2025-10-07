"""
Test main window with mock log data.

This script tests the complete UI with sample data loaded into the table.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication

from python.main_window import MainWindow
from python.log_entry import LogEntry, LogLevel


def main():
    """Run the main window test with mock data."""
    print("=" * 60)
    print("MainWindow Test - With Mock Data")
    print("=" * 60)

    app = QApplication(sys.argv)
    app.setApplicationName("LogReader Test")

    # Create main window
    window = MainWindow()

    # Create mock entries
    mock_entries = [
        LogEntry("16:29:40.318", LogLevel.DEBUG, "Vulkan loader version: 1.4.304", "Vulkan.cpp", "initVulkan", 92),
        LogEntry("16:29:40.587", LogLevel.INFO, "Supported instance extensions:", "Vulkan.cpp", "initVulkan", 106),
        LogEntry("16:29:40.601", LogLevel.INFO, "  VK_KHR_surface", "Vulkan.cpp", "initVulkan", 108),
        LogEntry("16:29:40.615", LogLevel.WARN, "Validation layer not available", "Vulkan.cpp", "checkLayers", 124),
        LogEntry("16:29:40.629", LogLevel.ERROR, "Failed to create surface", "Vulkan.cpp", "createSurface", 156),
        LogEntry("16:29:40.643", LogLevel.DEBUG, "Physical device count: 2", "Vulkan.cpp", "pickDevice", 178),
        LogEntry("16:29:40.657", LogLevel.INFO, "Selected device: NVIDIA GeForce RTX 3080", "Vulkan.cpp", "pickDevice", 192),
        LogEntry("16:29:40.671", LogLevel.DEBUG, "Queue family count: 3", "Vulkan.cpp", "findQueues", 210),
        LogEntry("16:29:40.685", LogLevel.WARN, "No transfer queue available", "Vulkan.cpp", "findQueues", 225),
        LogEntry("16:29:40.699", LogLevel.INFO, "Graphics queue index: 0", "Vulkan.cpp", "findQueues", 230),
    ]

    # Load mock data into the table
    window._log_model.set_entries(mock_entries)
    window._update_entry_count(len(mock_entries), len(mock_entries))
    window._update_status(f"Loaded {len(mock_entries)} mock entries")

    print(f"\n[OK] Loaded {len(mock_entries)} mock entries into table")
    print("[OK] Window should display:")
    print("  - Color-coded log levels")
    print("  - Entry count in status")
    print("  - All table columns properly formatted")
    print("\nClose the window to exit...")

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
