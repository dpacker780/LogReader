"""
Data models for LogReader application.

This module defines the core data structures used throughout the application:
- LogLevel: String-based log level (replaces enum for v1.1 dynamic tags)
- LogEntry: Dataclass representing a single parsed log entry

Version 1.1: LogLevel is now a simple string wrapper to support dynamic tags
from configuration, not a fixed enum.
"""

from dataclasses import dataclass
from typing import Optional


class LogLevel:
    """
    Represents a log severity level.

    Version 1.1: Changed from Enum to simple string wrapper to support
    dynamic tag names from configuration.
    """

    def __init__(self, name: str):
        """
        Initialize a LogLevel.

        Args:
            name: Tag name (e.g., "DEBUG", "INFO", "VERBOSE")
        """
        self.value = name.upper()

    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """
        Convert a string to a LogLevel.

        Args:
            level_str: String representation of the log level (case-insensitive)

        Returns:
            LogLevel instance

        Example:
            >>> LogLevel.from_string("DEBUG")
            LogLevel("DEBUG")
            >>> LogLevel.from_string("verbose")
            LogLevel("VERBOSE")
        """
        if not level_str:
            return cls("UNKNOWN")
        return cls(level_str.upper())

    def __str__(self) -> str:
        """Return the string value of the log level."""
        return self.value

    def __repr__(self) -> str:
        """Return representation of LogLevel."""
        return f'LogLevel("{self.value}")'

    def __eq__(self, other) -> bool:
        """Check equality with another LogLevel or string."""
        if isinstance(other, LogLevel):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.upper()
        return False

    def __hash__(self) -> int:
        """Make LogLevel hashable for use in dicts/sets."""
        return hash(self.value)


@dataclass
class LogEntry:
    """
    Represents a single log entry parsed from a log file.

    Attributes:
        timestamp: Time when the log entry was created (e.g., "16:29:40.318")
        level: Severity level of the log entry (LogLevel instance)
        message: The log message content
        source_file: Name of the source file that generated the log
        source_function: Name of the function that generated the log
        source_line: Line number in the source file
        line_number: Line number in the original log file (1-based)

    Example:
        >>> entry = LogEntry(
        ...     timestamp="16:29:40.318",
        ...     level=LogLevel("DEBUG"),
        ...     message="Vulkan loader version: 1.4.304",
        ...     source_file="Vulkan.cpp",
        ...     source_function="initVulkan",
        ...     source_line=92,
        ...     line_number=42
        ... )
    """

    timestamp: str
    level: LogLevel
    message: str
    source_file: str
    source_function: str
    source_line: int
    line_number: int = 0  # Default to 0 for backward compatibility

    def __post_init__(self):
        """Validate data after initialization."""
        if not isinstance(self.level, LogLevel):
            raise TypeError(f"level must be LogLevel, got {type(self.level)}")
        if self.source_line < 0:
            raise ValueError(f"source_line must be non-negative, got {self.source_line}")

    def format_source_info(self) -> str:
        """
        Format the source information as a string.

        Returns:
            Formatted string: "source_file:source_line"

        Example:
            >>> entry.format_source_info()
            "Vulkan.cpp:92"
        """
        return f"{self.source_file}:{self.source_line}"

    def format_full_source_info(self) -> str:
        """
        Format the complete source information including function name.

        Returns:
            Formatted string: "source_file -> source_function(): source_line"

        Example:
            >>> entry.format_full_source_info()
            "Vulkan.cpp -> initVulkan(): 92"
        """
        return f"{self.source_file} -> {self.source_function}(): {self.source_line}"

    def to_clipboard_format(self) -> str:
        """
        Format the log entry for clipboard export.

        Returns:
            Formatted string suitable for clipboard: "[timestamp][LEVEL]: message | source_info"

        Example:
            >>> entry.to_clipboard_format()
            "[16:29:40.318][DEBUG]: Vulkan loader version: 1.4.304 | Vulkan.cpp:92"
        """
        return f"[{self.timestamp}][{self.level.value:>6}]: {self.message} | {self.format_source_info()}"
