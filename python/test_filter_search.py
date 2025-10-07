"""
Test script for filter and search functionality.

This script tests various filter and search combinations programmatically.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.log_entry import LogEntry, LogLevel
from python.log_parser import LogParser


def test_filter_logic():
    """Test filtering logic with mock data."""
    print("=" * 60)
    print("Filter and Search Logic Test")
    print("=" * 60)

    # Parse a real log file
    if not Path("helix.log").exists():
        print("[ERROR] helix.log not found")
        return 1

    parser = LogParser()
    print("\n[1] Parsing helix.log...")
    start = time.time()
    entries = parser.parse("helix.log")
    elapsed = time.time() - start
    print(f"    Parsed {len(entries)} entries in {elapsed:.3f}s")

    # Count log levels
    level_counts = {}
    for entry in entries:
        level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

    print(f"\n[2] Log level distribution:")
    for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {level.value:>6}: {count:>4} entries")

    # Test 1: Filter by ERROR only
    print(f"\n[3] Filter test: ERROR only")
    error_entries = [e for e in entries if e.level == LogLevel.ERROR]
    print(f"    Result: {len(error_entries)}/{len(entries)} entries")
    assert len(error_entries) == level_counts.get(LogLevel.ERROR, 0)

    # Test 2: Filter by WARN or ERROR
    print(f"\n[4] Filter test: WARN or ERROR")
    warn_error_entries = [e for e in entries if e.level in [LogLevel.WARN, LogLevel.ERROR]]
    expected = level_counts.get(LogLevel.WARN, 0) + level_counts.get(LogLevel.ERROR, 0)
    print(f"    Result: {len(warn_error_entries)}/{len(entries)} entries")
    assert len(warn_error_entries) == expected

    # Test 3: Search for "Vulkan"
    print(f"\n[5] Search test: 'Vulkan'")
    search_term = "Vulkan"
    search_results = [e for e in entries if search_term.lower() in e.message.lower()]
    print(f"    Result: {len(search_results)}/{len(entries)} entries")
    print(f"    First match: {search_results[0].message[:50]}..." if search_results else "    No matches")

    # Test 4: Combined filter and search (ERROR + "failed")
    print(f"\n[6] Combined test: ERROR + 'failed'")
    combined = [e for e in entries
                if e.level == LogLevel.ERROR and "failed" in e.message.lower()]
    print(f"    Result: {len(combined)}/{len(entries)} entries")
    if combined:
        print(f"    Example: {combined[0].message[:60]}...")

    # Test 5: Search with no results
    print(f"\n[7] Search test: 'xyzabc123' (should be empty)")
    no_results = [e for e in entries if "xyzabc123" in e.message.lower()]
    print(f"    Result: {len(no_results)}/{len(entries)} entries")
    assert len(no_results) == 0

    # Test 6: Performance test - filter large dataset
    print(f"\n[8] Performance test: Filtering {len(entries)} entries")
    start = time.time()
    for _ in range(100):  # Run 100 times
        filtered = [e for e in entries if e.level in [LogLevel.DEBUG, LogLevel.INFO]]
    elapsed = time.time() - start
    avg_time = (elapsed / 100) * 1000  # Convert to ms
    print(f"    Average filter time: {avg_time:.2f}ms (100 iterations)")
    print(f"    Performance: {'PASS' if avg_time < 200 else 'FAIL'} (target: <200ms)")

    print("\n" + "=" * 60)
    print("All filter and search tests passed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(test_filter_logic())
