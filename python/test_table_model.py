"""
Test script for LogTableModel with mock data.

This script creates a window with the table model populated with sample log entries
to verify color coding and display functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QTableView
from PyQt6.QtCore import Qt

from python.log_entry import LogEntry, LogLevel
from python.log_table_model import LogTableModel


def create_mock_entries():
    """Create sample log entries for testing."""
    entries = [
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
        LogEntry("16:29:40.713", LogLevel.DEBUG, "Creating logical device", "Vulkan.cpp", "createDevice", 245),
        LogEntry("16:29:40.727", LogLevel.INFO, "Device created successfully", "Vulkan.cpp", "createDevice", 268),
        LogEntry("16:29:40.741", LogLevel.HEADER, "=== Initialization Complete ===", "Main.cpp", "main", 42),
        LogEntry("16:29:40.755", LogLevel.DEBUG, "Entering main loop", "Main.cpp", "main", 48),
        LogEntry("16:29:40.769", LogLevel.ERROR, "Out of memory", "Renderer.cpp", "allocateBuffer", 312),
        LogEntry("16:29:40.783", LogLevel.FOOTER, "=== Shutdown ===", "Main.cpp", "main", 95),
    ]
    return entries


def main():
    """Run the table model test."""
    print("=" * 60)
    print("LogTableModel Test - Displaying Mock Data")
    print("=" * 60)

    app = QApplication(sys.argv)

    # Create mock entries
    entries = create_mock_entries()
    print(f"\nCreated {len(entries)} mock log entries")

    # Create table model
    model = LogTableModel()
    model.set_entries(entries)
    print(f"Model has {model.rowCount()} rows and {model.columnCount()} columns")

    # Print entry counts
    print(f"Total entries: {model.get_total_entry_count()}")
    print(f"Filtered entries: {model.get_filtered_entry_count()}")

    # Test filtering (show only ERROR and WARN)
    error_warn_indices = [
        i for i, entry in enumerate(entries)
        if entry.level in [LogLevel.ERROR, LogLevel.WARN]
    ]
    model.set_filtered_indices(error_warn_indices)
    print(f"\nAfter filtering to ERROR/WARN: {model.get_filtered_entry_count()} entries")

    # Reset to show all
    model.set_filtered_indices(list(range(len(entries))))

    # Create window with table view
    window = QMainWindow()
    window.setWindowTitle("LogTableModel Test - Mock Data")
    window.setGeometry(100, 100, 1000, 600)

    table_view = QTableView()
    table_view.setModel(model)
    table_view.setAlternatingRowColors(True)
    table_view.verticalHeader().setVisible(False)

    # Set column widths
    table_view.setColumnWidth(0, 120)  # Timestamp
    table_view.setColumnWidth(1, 80)   # Level
    table_view.setColumnWidth(3, 250)  # Source

    window.setCentralWidget(table_view)
    window.show()

    print("\n[OK] Window opened with mock data")
    print("[OK] Verify that:")
    print("  - All 16 entries are displayed")
    print("  - Colors are correct:")
    print("    - DEBUG: Cyan")
    print("    - INFO: Green")
    print("    - WARN: Yellow")
    print("    - ERROR: Red")
    print("    - HEADER/FOOTER: Blue")
    print("\nClose the window to exit...")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
