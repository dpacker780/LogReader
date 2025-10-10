"""
Live log monitoring for LogReader application.

This module provides functionality to detect file changes and determine
whether a log file was appended to or completely replaced.
"""

import hashlib
from pathlib import Path
from enum import Enum, auto
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of file changes detected."""
    NEW_FILE = auto()      # File was replaced/truncated/rotated
    APPEND = auto()        # New content was appended
    NO_CHANGE = auto()     # File unchanged (spurious notification)


class LiveLogMonitor:
    """
    Monitors log file changes and detects modification type.

    Uses file size and first-line fingerprinting to efficiently detect
    whether a file was replaced or appended to.

    This approach is much more efficient than hashing every line, while
    still being reliable for real-world log file scenarios.
    """

    def __init__(self):
        """Initialize the monitor with empty state."""
        self._live_mode: bool = False
        self._last_file_size: int = 0
        self._last_line_count: int = 0
        self._first_line_hash: str = ""
        self._current_file_path: str = ""
        self._last_modified_time: float = 0.0  # Track last modification timestamp

    def enable_live_mode(self, enabled: bool):
        """
        Enable or disable live update mode.

        Args:
            enabled: True to enable live mode, False to disable
        """
        self._live_mode = enabled
        logger.info(f"Live mode {'enabled' if enabled else 'disabled'}")

    def is_live_mode(self) -> bool:
        """
        Check if live mode is currently enabled.

        Returns:
            True if live mode is active, False otherwise
        """
        return self._live_mode

    def initialize_file_state(self, file_path: str, line_count: int):
        """
        Initialize tracking state for a newly loaded file.

        Call this after successfully parsing a log file for the first time.

        Args:
            file_path: Path to the log file being monitored
            line_count: Number of lines/entries parsed from the file
        """
        self._current_file_path = file_path
        self._last_line_count = line_count

        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Cannot initialize state - file not found: {file_path}")
                return

            # Store file size and modification time
            stat = path.stat()
            self._last_file_size = stat.st_size
            self._last_modified_time = stat.st_mtime

            # Compute first line hash as fingerprint
            first_line = self._read_first_line(file_path)
            self._first_line_hash = self._compute_hash(first_line)

            logger.info(f"Initialized file state: size={self._last_file_size}, "
                       f"mtime={self._last_modified_time}, lines={line_count}, hash={self._first_line_hash[:8]}...")

        except Exception as e:
            logger.error(f"Error initializing file state: {e}")

    def detect_change_type(self, file_path: str) -> ChangeType:
        """
        Detect what type of change occurred to the monitored file.

        This method uses modification time, file size, and first-line fingerprinting
        to efficiently determine if the file was replaced or appended to.

        Args:
            file_path: Path to the file that changed

        Returns:
            ChangeType indicating the type of change detected
        """
        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return ChangeType.NEW_FILE

            # Get current file stats
            stat = path.stat()
            current_size = stat.st_size
            current_mtime = stat.st_mtime

            # Early exit: Check modification time FIRST (fastest check)
            # If mtime hasn't changed, nothing has changed (spurious notification)
            if abs(current_mtime - self._last_modified_time) < 0.001:  # Within 1ms
                logger.debug(f"Modification time unchanged: {current_mtime} (NO_CHANGE - spurious)")
                return ChangeType.NO_CHANGE

            # Case 1: File was truncated or replaced (size decreased)
            if current_size < self._last_file_size:
                logger.info(f"File size decreased: {self._last_file_size} -> {current_size} (NEW_FILE)")
                return ChangeType.NEW_FILE

            # Case 2: File size unchanged (in-place edit or metadata change)
            if current_size == self._last_file_size:
                logger.debug(f"File size unchanged but mtime changed: {current_size} (NO_CHANGE)")
                return ChangeType.NO_CHANGE

            # Case 3: File size increased - check if it's the same file
            # Read first line and compare hash
            first_line = self._read_first_line(file_path)
            first_hash = self._compute_hash(first_line)

            if first_hash != self._first_line_hash:
                logger.info(f"First line changed: {self._first_line_hash[:8]}... -> {first_hash[:8]}... (NEW_FILE)")
                return ChangeType.NEW_FILE

            # Same first line, larger file = append
            bytes_added = current_size - self._last_file_size
            logger.info(f"File appended: +{bytes_added} bytes (APPEND)")
            return ChangeType.APPEND

        except Exception as e:
            logger.error(f"Error detecting change type: {e}")
            # On error, treat as new file to trigger full reload (safe fallback)
            return ChangeType.NEW_FILE

    def get_append_start_position(self) -> int:
        """
        Get the file position where new content starts (for append mode).

        Returns:
            Byte position to seek to when reading appended content
        """
        return self._last_file_size

    def get_next_line_number(self) -> int:
        """
        Get the line number for the next log entry (for append mode).

        Returns:
            Line number (1-based) for the next entry to be parsed
        """
        return self._last_line_count + 1

    def update_state(self, new_size: int, new_line_count: int, new_mtime: float = None):
        """
        Update tracking state after successfully processing file changes.

        Call this after parsing appended content or reloading the file.

        Args:
            new_size: New file size in bytes
            new_line_count: New total number of lines/entries
            new_mtime: New modification time (if None, will re-read from file)
        """
        self._last_file_size = new_size
        self._last_line_count = new_line_count

        # Update modification time
        if new_mtime is not None:
            self._last_modified_time = new_mtime
        elif self._current_file_path:
            try:
                self._last_modified_time = Path(self._current_file_path).stat().st_mtime
            except Exception as e:
                logger.warning(f"Could not update mtime: {e}")

        logger.debug(f"Updated state: size={new_size}, mtime={self._last_modified_time}, lines={new_line_count}")

    def _read_first_line(self, file_path: str) -> str:
        """
        Read the first non-empty line from a file.

        Args:
            file_path: Path to the file

        Returns:
            First non-empty line content, or empty string if file is empty
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        return line
                return ""  # Empty file

        except Exception as e:
            logger.error(f"Error reading first line: {e}")
            return ""

    def _compute_hash(self, content: str) -> str:
        """
        Compute MD5 hash of content for fingerprinting.

        Args:
            content: String content to hash

        Returns:
            Hex digest of MD5 hash
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
