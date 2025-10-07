"""
Test script for LogParser functionality.

Tests both synchronous and asynchronous parsing with real log files.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.log_parser import LogParser
from python.log_entry import LogLevel


def test_sync_parse(file_path: str):
    """Test synchronous parsing."""
    print(f"\nTesting synchronous parse of: {file_path}")
    print("-" * 60)

    parser = LogParser()

    try:
        start_time = time.time()
        entries = parser.parse(file_path)
        elapsed = time.time() - start_time

        print(f"[OK] Parsed {len(entries)} entries in {elapsed:.3f}s")

        if entries:
            # Show first entry
            first = entries[0]
            print(f"\nFirst entry:")
            print(f"  Timestamp: {first.timestamp}")
            print(f"  Level: {first.level}")
            print(f"  Message: {first.message}")
            print(f"  Source: {first.format_full_source_info()}")

            # Show log level distribution
            level_counts = {}
            for entry in entries:
                level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

            print(f"\nLog level distribution:")
            for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {level.value:>6}: {count:>6} entries")

        return True

    except FileNotFoundError:
        print(f"[FAIL] File not found: {file_path}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_async_parse(file_path: str):
    """Test asynchronous parsing."""
    print(f"\n\nTesting asynchronous parse of: {file_path}")
    print("-" * 60)

    parser = LogParser()
    progress_updates = []
    final_entries = []

    def on_progress(status: str, entries):
        progress_updates.append((status, len(entries)))
        print(f"  Progress: {status} ({len(entries)} entries)")
        nonlocal final_entries
        final_entries = entries.copy()  # Keep a copy

    try:
        start_time = time.time()

        # Start async parsing
        parser.parse_async(file_path, on_progress)

        # Wait for parsing to complete
        while parser.is_parsing():
            time.sleep(0.1)

        elapsed = time.time() - start_time

        print(f"\n[OK] Async parsing completed in {elapsed:.3f}s")
        print(f"[OK] Received {len(progress_updates)} progress updates")
        print(f"[OK] Final entry count: {len(final_entries)}")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cancel_parsing():
    """Test cancelling async parsing."""
    print(f"\n\nTesting parse cancellation")
    print("-" * 60)

    parser = LogParser()
    progress_count = 0

    def on_progress(status: str, entries):
        nonlocal progress_count
        progress_count += 1
        print(f"  Progress update {progress_count}: {status}")

    # Start parsing a large file
    parser.parse_async("helix.log", on_progress)

    # Wait a bit then cancel
    time.sleep(0.2)
    print("  Requesting cancellation...")
    parser.stop_parsing()

    print(f"[OK] Parsing stopped after {progress_count} updates")
    return True


def main():
    """Run parser tests."""
    print("=" * 60)
    print("LogParser Test Suite")
    print("=" * 60)

    test_files = [
        "test_ascii_format.log",
        "helix.log",
    ]

    results = []

    # Test synchronous parsing
    for file_path in test_files:
        if Path(file_path).exists():
            results.append(test_sync_parse(file_path))
        else:
            print(f"\n[SKIP] File not found: {file_path}")

    # Test asynchronous parsing
    if Path("helix.log").exists():
        results.append(test_async_parse("helix.log"))
    else:
        print("\n[SKIP] helix.log not found for async test")

    # Test cancellation
    if Path("helix.log").exists():
        results.append(test_cancel_parsing())

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
