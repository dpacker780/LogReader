"""
Log file parser for LogReader application.

This module handles parsing log files in the ASCII field separator format:
    timestamp<FS>LEVEL<FS>message<FS>source_file -> function(): line_number

Where <FS> is ASCII character 31 (0x1F).
"""

import re
import threading
from pathlib import Path
from typing import List, Callable, Optional
import logging

try:
    from .log_entry import LogEntry, LogLevel
    from .config import ConfigManager
except ImportError:
    from log_entry import LogEntry, LogLevel
    from config import ConfigManager


logger = logging.getLogger(__name__)


class LogParser:
    """
    Parser for log files using ASCII field separator format.

    Supports both synchronous and asynchronous parsing with progress callbacks.
    Asynchronous parsing uses batched processing to prevent UI blocking.
    """

    # ASCII field separator character
    FIELD_SEPARATOR = chr(31)  # 0x1F

    # Batch size for async parsing (lines per batch)
    BATCH_SIZE = 5000

    # Maximum lines to parse per append operation (prevents UI freeze on huge appends)
    MAX_APPEND_LINES = 10000

    # Regex pattern for parsing source info (legacy 4-field format): "source_file -> function(): line_number"
    # Note: No longer used in new 6-field format
    SOURCE_INFO_PATTERN = re.compile(r'(.*)\s*->\s*(.*)\(\):\s*(\d+)')

    def __init__(self):
        """Initialize the parser."""
        self._parsing_active: bool = False
        self._stop_requested: threading.Event = threading.Event()
        self._parser_thread: Optional[threading.Thread] = None

    def parse(self, file_path: str) -> List[LogEntry]:
        """
        Parse a log file synchronously.

        Args:
            file_path: Path to the log file to parse

        Returns:
            List of parsed LogEntry objects

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file

        Example:
            >>> parser = LogParser()
            >>> entries = parser.parse("test.log")
            >>> print(f"Parsed {len(entries)} entries")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        logger.info(f"Starting synchronous parse of: {file_path}")

        entries: List[LogEntry] = []
        line_count = 0
        matched_count = 0

        try:
            with path.open('r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    line = line.rstrip('\n\r')

                    entry = self._parse_line(line, line_count)
                    if entry:
                        entries.append(entry)
                        matched_count += 1

            failed_count = line_count - matched_count
            logger.info(f"Parsed {line_count} lines: {matched_count} matched, {failed_count} failed")
            if failed_count > 0:
                logger.warning(f"  {failed_count} lines failed to parse (check format)")
            return entries

        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise

    def parse_async(
        self,
        file_path: str,
        callback: Callable[[str, List[LogEntry]], None]
    ) -> None:
        """
        Parse a log file asynchronously with progress updates.

        This method spawns a background thread to parse the file in batches,
        calling the callback function periodically with progress updates.

        Args:
            file_path: Path to the log file to parse
            callback: Function called with (status_message, current_entries)
                     Status messages: "Parsing... X% (Y lines)" or "Complete: X entries from Y lines"

        Example:
            >>> def on_progress(status, entries):
            ...     print(f"{status}: {len(entries)} entries so far")
            >>> parser = LogParser()
            >>> parser.parse_async("test.log", on_progress)
        """
        # Stop any existing parsing
        self.stop_parsing()

        # Start new parsing thread
        self._parser_thread = threading.Thread(
            target=self._parse_async_worker,
            args=(file_path, callback),
            daemon=True
        )
        self._parser_thread.start()

    def _parse_async_worker(
        self,
        file_path: str,
        callback: Callable[[str, List[LogEntry]], None]
    ) -> None:
        """
        Worker function for asynchronous parsing (runs in separate thread).

        Args:
            file_path: Path to the log file to parse
            callback: Progress callback function
        """
        self._parsing_active = True
        self._stop_requested.clear()

        path = Path(file_path)

        if not path.exists():
            callback("Error: File not found", [])
            self._parsing_active = False
            return

        try:
            file_size = path.stat().st_size
            logger.info(f"Starting async parse of: {file_path} ({file_size} bytes)")

            entries: List[LogEntry] = []
            line_batch: List[str] = []
            total_lines = 0
            bytes_read = 0
            batch_start_line = 1  # Track starting line number for each batch

            callback("Starting parse... 0%", entries)

            with path.open('r', encoding='utf-8') as f:
                for line in f:
                    if self._stop_requested.is_set():
                        callback("Parsing cancelled", entries)
                        self._parsing_active = False
                        return

                    line = line.rstrip('\n\r')
                    line_batch.append(line)
                    total_lines += 1
                    bytes_read += len(line.encode('utf-8')) + 1  # +1 for newline

                    # Process batch when it reaches BATCH_SIZE
                    if len(line_batch) >= self.BATCH_SIZE:
                        batch_entries = self._parse_batch(line_batch, batch_start_line)
                        entries.extend(batch_entries)

                        # Calculate progress
                        progress = min(100, int((bytes_read * 100) / file_size)) if file_size > 0 else 100
                        status = f"Parsing... {progress}% ({total_lines} lines)"
                        callback(status, entries)

                        batch_start_line += len(line_batch)  # Update for next batch
                        line_batch.clear()

                        # Small delay to prevent UI blocking
                        threading.Event().wait(0.01)

                # Process remaining lines
                if line_batch and not self._stop_requested.is_set():
                    batch_entries = self._parse_batch(line_batch, batch_start_line)
                    entries.extend(batch_entries)

            if self._stop_requested.is_set():
                callback("Parsing cancelled", entries)
            else:
                failed_count = total_lines - len(entries)
                status = f"Complete: {len(entries)} entries from {total_lines} lines"
                callback(status, entries)
                logger.info(f"Async parse complete: {len(entries)} entries from {total_lines} lines")
                if failed_count > 0:
                    logger.warning(f"  {failed_count} lines failed to parse (check format)")

        except Exception as e:
            logger.error(f"Error in async parsing: {e}")
            callback(f"Error: {str(e)}", [])

        finally:
            self._parsing_active = False

    def _parse_batch(self, lines: List[str], start_line_number: int = 1) -> List[LogEntry]:
        """
        Parse a batch of lines.

        Args:
            lines: List of log file lines to parse
            start_line_number: Starting line number for this batch (1-based)

        Returns:
            List of parsed LogEntry objects
        """
        entries: List[LogEntry] = []

        for i, line in enumerate(lines):
            if self._stop_requested.is_set():
                break

            line_number = start_line_number + i
            entry = self._parse_line(line, line_number)
            if entry:
                entries.append(entry)

        return entries

    def _parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single log line.

        Expected format (new 6-field): timestamp<FS>LEVEL<FS>message<FS>file<FS>function<FS>line
        Example: "16:29:40.318<FS>DEBUG<FS>Vulkan loader version<FS>Vulkan.cpp<FS>initVulkan<FS>92"

        Args:
            line: A single line from the log file
            line_number: Line number in the original file (1-based)

        Returns:
            LogEntry object if parsing succeeds, None otherwise
        """
        # Skip empty lines
        if not line.strip():
            return None

        # Split by field separator
        fields = line.split(self.FIELD_SEPARATOR)

        # New format: Need exactly 6 fields: timestamp, level, message, file, function, line
        if len(fields) < 6:
            logger.warning(f"Line {line_number}: Invalid format (expected 6 fields, got {len(fields)})")
            logger.debug(f"  Content: {line[:100]}...")
            return None

        try:
            timestamp = fields[0]
            level_str = fields[1].strip()
            message = fields[2]
            source_file = fields[3].strip()
            source_function = fields[4].strip()
            source_line_str = fields[5].strip()

            # Parse log level (auto-create unknown tags)
            level = LogLevel.from_string(level_str)

            # Auto-register unknown tags in config with default gray color
            # This happens silently during parsing - user can customize later
            ConfigManager.get_or_create_tag(level.value)

            # Parse source line number
            try:
                source_line = int(source_line_str)
            except ValueError:
                logger.warning(f"Line {line_number}: Invalid line number '{source_line_str}'")
                source_line = 0

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source_file=source_file,
                source_function=source_function,
                source_line=source_line,
                line_number=line_number
            )

        except (IndexError, ValueError) as e:
            logger.warning(f"Line {line_number}: Parse error - {e}")
            logger.debug(f"  Content: {line[:100]}...")
            return None

    def is_parsing(self) -> bool:
        """
        Check if asynchronous parsing is currently in progress.

        Returns:
            True if parsing is active, False otherwise
        """
        return self._parsing_active

    def parse_append(
        self,
        file_path: str,
        start_position: int,
        start_line_number: int,
        max_lines: int = None
    ) -> List[LogEntry]:
        """
        Parse only appended content from a log file (synchronous).

        This method seeks to a specific byte position in the file and parses
        only the new content that was appended since the last read.

        Args:
            file_path: Path to the log file
            start_position: Byte position to start reading from
            start_line_number: Line number (1-based) for the first new line
            max_lines: Maximum number of lines to parse (default: MAX_APPEND_LINES)

        Returns:
            List of newly parsed LogEntry objects

        Example:
            >>> parser = LogParser()
            >>> # After initial parse, file grew from 1000 bytes with 50 lines
            >>> new_entries = parser.parse_append("test.log", 1000, 51)
        """
        if max_lines is None:
            max_lines = self.MAX_APPEND_LINES

        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found for append parse: {file_path}")
            return []

        try:
            logger.info(f"Parsing appended content from position {start_position}, "
                       f"starting at line {start_line_number}, max_lines={max_lines}")

            entries: List[LogEntry] = []
            line_number = start_line_number
            lines_read = 0

            with path.open('r', encoding='utf-8') as f:
                # Seek to the last known position
                f.seek(start_position)

                # Read and parse new lines (up to max_lines)
                for line in f:
                    if lines_read >= max_lines:
                        logger.warning(f"Reached max_lines limit ({max_lines}) - stopping append parse")
                        break

                    line = line.rstrip('\n\r')
                    entry = self._parse_line(line, line_number)
                    if entry:
                        entries.append(entry)
                    line_number += 1
                    lines_read += 1

            logger.info(f"Parsed {len(entries)} new entries from appended content ({lines_read} lines read)")
            return entries

        except Exception as e:
            logger.error(f"Error parsing appended content: {e}")
            return []

    def parse_append_async(
        self,
        file_path: str,
        start_position: int,
        start_line_number: int,
        callback: Callable[[str, List[LogEntry]], None],
        max_lines: int = None
    ) -> None:
        """
        Parse only appended content from a log file (asynchronous).

        Similar to parse_append() but runs in a background thread with progress callbacks.

        Args:
            file_path: Path to the log file
            start_position: Byte position to start reading from
            start_line_number: Line number (1-based) for the first new line
            callback: Function called with (status_message, new_entries)
            max_lines: Maximum number of lines to parse (default: MAX_APPEND_LINES)
        """
        if max_lines is None:
            max_lines = self.MAX_APPEND_LINES

        # Stop any existing parsing
        self.stop_parsing()

        # Start new parsing thread
        self._parser_thread = threading.Thread(
            target=self._parse_append_async_worker,
            args=(file_path, start_position, start_line_number, callback, max_lines),
            daemon=True
        )
        self._parser_thread.start()

    def _parse_append_async_worker(
        self,
        file_path: str,
        start_position: int,
        start_line_number: int,
        callback: Callable[[str, List[LogEntry]], None],
        max_lines: int
    ) -> None:
        """
        Worker function for asynchronous append parsing (runs in separate thread).

        Args:
            file_path: Path to the log file
            start_position: Byte position to start reading from
            start_line_number: Line number for first new line
            callback: Progress callback function
            max_lines: Maximum number of lines to parse
        """
        self._parsing_active = True
        self._stop_requested.clear()

        path = Path(file_path)

        if not path.exists():
            callback("Error: File not found", [])
            self._parsing_active = False
            return

        try:
            current_size = path.stat().st_size
            bytes_to_read = current_size - start_position

            logger.info(f"Starting async append parse: position={start_position}, "
                       f"bytes={bytes_to_read}, start_line={start_line_number}, max_lines={max_lines}")

            entries: List[LogEntry] = []
            line_batch: List[str] = []
            line_number = start_line_number
            bytes_read = 0
            lines_read = 0

            callback("Parsing new entries... 0%", [])

            with path.open('r', encoding='utf-8') as f:
                # Seek to last known position
                f.seek(start_position)

                for line in f:
                    if self._stop_requested.is_set():
                        callback("Append parse cancelled", entries)
                        self._parsing_active = False
                        return

                    # Check max lines limit
                    if lines_read >= max_lines:
                        logger.warning(f"Reached max_lines limit ({max_lines}) - stopping append parse")
                        status = f"Partial: +{len(entries)} entries (max limit reached)"
                        callback(status, entries)
                        break

                    line = line.rstrip('\n\r')
                    line_batch.append(line)
                    bytes_read += len(line.encode('utf-8')) + 1  # +1 for newline
                    lines_read += 1

                    # Process batch
                    if len(line_batch) >= self.BATCH_SIZE:
                        batch_entries = self._parse_batch(line_batch, line_number)
                        entries.extend(batch_entries)
                        line_number += len(line_batch)

                        # Calculate progress
                        progress = min(100, int((bytes_read * 100) / bytes_to_read)) if bytes_to_read > 0 else 100
                        status = f"Parsing new entries... {progress}% (+{len(entries)} new)"
                        callback(status, entries)

                        line_batch.clear()
                        threading.Event().wait(0.01)  # Small delay

                # Process remaining lines
                if line_batch and not self._stop_requested.is_set():
                    batch_entries = self._parse_batch(line_batch, line_number)
                    entries.extend(batch_entries)

            if self._stop_requested.is_set():
                callback("Append parse cancelled", entries)
            elif lines_read >= max_lines:
                status = f"Partial: +{len(entries)} entries (limit: {max_lines} lines)"
                callback(status, entries)
                logger.info(f"Append parse hit limit: {len(entries)} entries from {lines_read} lines")
            else:
                status = f"Complete: +{len(entries)} new entries"
                callback(status, entries)
                logger.info(f"Append parse complete: {len(entries)} new entries from {lines_read} lines")

        except Exception as e:
            logger.error(f"Error in async append parsing: {e}")
            callback(f"Error: {str(e)}", [])

        finally:
            self._parsing_active = False

    def stop_parsing(self) -> None:
        """
        Request cancellation of asynchronous parsing.

        This method signals the parser thread to stop and waits for it to finish.
        Safe to call even if no parsing is in progress.
        """
        if self._parsing_active:
            logger.info("Stopping async parsing...")
            self._stop_requested.set()

        if self._parser_thread and self._parser_thread.is_alive():
            self._parser_thread.join(timeout=2.0)

        self._parsing_active = False
        self._stop_requested.clear()
