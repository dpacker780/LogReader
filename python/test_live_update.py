"""
Test script for live update functionality.

This script demonstrates how to test the live log update feature by
simulating different types of file modifications.

Usage:
    1. Run LogReader: python python/main.py
    2. Open the test log file: test_live_update.log
    3. Enable Live Update Mode (Options → Live Update Mode)
    4. Run this script: python python/test_live_update.py
    5. Watch LogReader auto-update as this script modifies the log
"""

import time
import sys
from pathlib import Path

# Field separator (ASCII 31)
FS = chr(31)

def create_test_log():
    """Create initial test log file."""
    log_path = Path("test_live_update.log")

    print("Creating initial test log...")
    with open(log_path, 'w', encoding='utf-8') as f:
        # Write initial entries
        for i in range(1, 11):
            timestamp = f"10:00:{i:02d}.000"
            f.write(f"{timestamp}{FS}INFO{FS}Initial entry {i}{FS}TestFile.py{FS}test_func{FS}{i}\n")

    print(f"✓ Created {log_path} with 10 initial entries")
    return log_path


def append_entries(log_path: Path, start_num: int, count: int):
    """Append new entries to the log file."""
    print(f"\nAppending {count} new entries (#{start_num}-#{start_num+count-1})...")

    with open(log_path, 'a', encoding='utf-8') as f:
        for i in range(start_num, start_num + count):
            timestamp = f"10:00:{i:02d}.000"
            f.write(f"{timestamp}{FS}DEBUG{FS}Appended entry {i}{FS}TestFile.py{FS}test_func{FS}{i}\n")

    print(f"✓ Appended {count} entries")


def replace_log(log_path: Path):
    """Replace the entire log file (truncate and write new content)."""
    print("\nReplacing entire log file (NEW FILE scenario)...")

    with open(log_path, 'w', encoding='utf-8') as f:
        # Write completely new content
        for i in range(1, 6):
            timestamp = f"11:00:{i:02d}.000"
            f.write(f"{timestamp}{FS}WARN{FS}Replaced entry {i}{FS}NewFile.py{FS}new_func{FS}{i}\n")

    print(f"✓ Replaced log with 5 new entries")


def main():
    """Run live update test scenarios."""
    print("=" * 60)
    print("LogReader Live Update Test Script")
    print("=" * 60)
    print()
    print("SETUP INSTRUCTIONS:")
    print("1. Run LogReader: python python/main.py")
    print("2. Open 'test_live_update.log' in LogReader")
    print("3. Enable: Options → Live Update Mode")
    print("4. Watch the log viewer update automatically!")
    print()
    input("Press Enter when ready to start the test...")
    print()

    # Create initial log
    log_path = create_test_log()

    print("\nWaiting 3 seconds for you to open the file in LogReader...")
    time.sleep(3)

    # Test 1: Append entries
    print("\n" + "=" * 60)
    print("TEST 1: APPEND MODE (adding new entries)")
    print("=" * 60)
    input("Press Enter to append 5 entries...")
    append_entries(log_path, 11, 5)
    print("→ LogReader should show +5 entries (total: 15)")
    time.sleep(2)

    # Test 2: Append more entries
    input("\nPress Enter to append 10 more entries...")
    append_entries(log_path, 16, 10)
    print("→ LogReader should show +10 entries (total: 25)")
    time.sleep(2)

    # Test 3: Replace log
    print("\n" + "=" * 60)
    print("TEST 2: NEW FILE MODE (replacing entire log)")
    print("=" * 60)
    input("Press Enter to replace the entire log...")
    replace_log(log_path)
    print("→ LogReader should detect NEW FILE and reload (total: 5 new entries)")
    time.sleep(2)

    # Test 4: Append to replaced log
    print("\n" + "=" * 60)
    print("TEST 3: APPEND AFTER REPLACEMENT")
    print("=" * 60)
    input("Press Enter to append 3 entries to the new log...")
    append_entries(log_path, 6, 3)
    print("→ LogReader should show +3 entries (total: 8)")
    time.sleep(2)

    # Test 5: Rapid appends
    print("\n" + "=" * 60)
    print("TEST 4: RAPID APPENDS (stress test)")
    print("=" * 60)
    input("Press Enter to rapidly append 50 entries...")
    print("Appending 50 entries in 5 batches...")
    for batch in range(5):
        start = 9 + (batch * 10)
        append_entries(log_path, start, 10)
        time.sleep(0.5)  # Small delay between batches
    print("→ LogReader should show all 50 new entries (total: 58)")

    print("\n" + "=" * 60)
    print("✓ All tests complete!")
    print("=" * 60)
    print()
    print(f"Test log file: {log_path.absolute()}")
    print("You can delete this file when done testing.")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
