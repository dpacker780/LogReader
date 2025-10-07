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
except ImportError:
    from log_entry import LogEntry, LogLevel


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

    # Regex pattern for parsing source info: "source_file -> function(): line_number"
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

            logger.info(f"Parsed {line_count} lines, {matched_count} matched")
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
                status = f"Complete: {len(entries)} entries from {total_lines} lines"
                callback(status, entries)
                logger.info(f"Async parse complete: {len(entries)} entries")

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

        Expected format: timestamp<FS>LEVEL<FS>message<FS>source_info
        Where source_info is: "source_file -> function(): line_number"

        Args:
            line: A single line from the log file
            line_number: Line number in the original file (1-based)

        Returns:
            LogEntry object if parsing succeeds, None otherwise
        """
        # Split by field separator
        fields = line.split(self.FIELD_SEPARATOR)

        # Need at least 4 fields: timestamp, level, message, source_info
        if len(fields) < 4:
            return None

        try:
            timestamp = fields[0]
            level_str = fields[1].strip()
            message = fields[2]
            source_info = fields[3]

            # Parse log level
            level = LogLevel.from_string(level_str)
            if level is None:
                logger.debug(f"Unknown log level: {level_str}")
                level = LogLevel.DEBUG  # Default fallback

            # Parse source info using regex
            match = self.SOURCE_INFO_PATTERN.match(source_info)
            if match:
                source_file = match.group(1).strip()
                source_function = match.group(2).strip()
                source_line = int(match.group(3))
            else:
                # Fallback if source info doesn't match expected format
                source_file = source_info
                source_function = "unknown"
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
            logger.debug(f"Failed to parse line: {e}")
            return None

    def is_parsing(self) -> bool:
        """
        Check if asynchronous parsing is currently in progress.

        Returns:
            True if parsing is active, False otherwise
        """
        return self._parsing_active

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
