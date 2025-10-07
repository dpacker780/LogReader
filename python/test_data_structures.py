"""
Unit tests for LogReader data structures and configuration management.

Run with: python -m pytest python/test_data_structures.py
Or simply: python python/test_data_structures.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.log_entry import LogLevel, LogEntry
from python.config import ConfigManager


def test_log_level_enum():
    """Test LogLevel enum values."""
    print("Testing LogLevel enum...")

    assert LogLevel.DEBUG.value == "DEBUG"
    assert LogLevel.INFO.value == "INFO"
    assert LogLevel.WARN.value == "WARN"
    assert LogLevel.ERROR.value == "ERROR"
    assert LogLevel.HEADER.value == "HEADER"
    assert LogLevel.FOOTER.value == "FOOTER"

    print("  [OK] All LogLevel values correct")


def test_log_level_from_string():
    """Test LogLevel.from_string() method."""
    print("Testing LogLevel.from_string()...")

    assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
    assert LogLevel.from_string("debug") == LogLevel.DEBUG
    assert LogLevel.from_string("INFO") == LogLevel.INFO
    assert LogLevel.from_string("invalid") is None
    assert LogLevel.from_string("") is None

    print("  [OK] from_string() works correctly")


def test_log_entry_creation():
    """Test LogEntry creation and validation."""
    print("Testing LogEntry creation...")

    entry = LogEntry(
        timestamp="16:29:40.318",
        level=LogLevel.DEBUG,
        message="Test message",
        source_file="test.cpp",
        source_function="testFunc",
        source_line=42
    )

    assert entry.timestamp == "16:29:40.318"
    assert entry.level == LogLevel.DEBUG
    assert entry.message == "Test message"
    assert entry.source_file == "test.cpp"
    assert entry.source_function == "testFunc"
    assert entry.source_line == 42

    print("  [OK] LogEntry created successfully")


def test_log_entry_validation():
    """Test LogEntry validation."""
    print("Testing LogEntry validation...")

    # Test negative line number
    try:
        entry = LogEntry(
            timestamp="16:29:40.318",
            level=LogLevel.DEBUG,
            message="Test",
            source_file="test.cpp",
            source_function="testFunc",
            source_line=-1
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  [OK] Negative line number rejected")

    # Test invalid level type
    try:
        entry = LogEntry(
            timestamp="16:29:40.318",
            level="DEBUG",  # String instead of LogLevel
            message="Test",
            source_file="test.cpp",
            source_function="testFunc",
            source_line=42
        )
        assert False, "Should have raised TypeError"
    except TypeError:
        print("  [OK] Invalid level type rejected")


def test_log_entry_formatting():
    """Test LogEntry formatting methods."""
    print("Testing LogEntry formatting...")

    entry = LogEntry(
        timestamp="16:29:40.318",
        level=LogLevel.DEBUG,
        message="Vulkan loader version: 1.4.304",
        source_file="Vulkan.cpp",
        source_function="initVulkan",
        source_line=92
    )

    # Test format_source_info()
    assert entry.format_source_info() == "Vulkan.cpp:92"
    print("  [OK] format_source_info() correct")

    # Test format_full_source_info()
    assert entry.format_full_source_info() == "Vulkan.cpp -> initVulkan(): 92"
    print("  [OK] format_full_source_info() correct")

    # Test to_clipboard_format()
    expected = "[16:29:40.318][ DEBUG]: Vulkan loader version: 1.4.304 | Vulkan.cpp:92"
    assert entry.to_clipboard_format() == expected
    print("  [OK] to_clipboard_format() correct")


def test_config_save_load():
    """Test ConfigManager save and load."""
    print("Testing ConfigManager save/load...")

    # Clean up any existing config
    ConfigManager.delete_config()

    # Test load with no config file (should return default)
    path = ConfigManager.load_last_file_path()
    assert path == ConfigManager.DEFAULT_FILE_PATH
    print("  [OK] Load with no config returns default")

    # Test save
    test_path = "test_log_file.txt"
    success = ConfigManager.save_last_file_path(test_path)
    assert success
    print("  [OK] Save successful")

    # Test load after save (file doesn't exist, should return default)
    path = ConfigManager.load_last_file_path()
    assert path == ConfigManager.DEFAULT_FILE_PATH
    print("  [OK] Load non-existent file returns default")

    # Test save with existing file
    Path("test_existing.log").touch()
    success = ConfigManager.save_last_file_path("test_existing.log")
    assert success
    path = ConfigManager.load_last_file_path()
    assert path == "test_existing.log"
    print("  [OK] Load existing file works")

    # Clean up
    Path("test_existing.log").unlink()
    ConfigManager.delete_config()
    print("  [OK] Cleanup successful")


def test_config_edge_cases():
    """Test ConfigManager edge cases."""
    print("Testing ConfigManager edge cases...")

    ConfigManager.delete_config()

    # Test save empty path
    success = ConfigManager.save_last_file_path("")
    assert not success
    print("  [OK] Empty path rejected")

    # Test config_exists()
    assert not ConfigManager.config_exists()
    ConfigManager.save_last_file_path("test.txt")
    assert ConfigManager.config_exists()
    print("  [OK] config_exists() works")

    # Clean up
    ConfigManager.delete_config()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running LogReader Data Structure Tests")
    print("=" * 60)
    print()

    tests = [
        test_log_level_enum,
        test_log_level_from_string,
        test_log_entry_creation,
        test_log_entry_validation,
        test_log_entry_formatting,
        test_config_save_load,
        test_config_edge_cases,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"  [FAIL] {test_func.__name__}: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"  [ERROR] {test_func.__name__}: {e}")
            failed += 1
            print()

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
