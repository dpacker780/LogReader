"""
Configuration management for LogReader application.

This module handles loading and saving application configuration,
including last opened files and customizable log tags.

Version 1.1 introduces JSON-based configuration with automatic migration
from the legacy text format.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class LogTag:
    """Represents a log level tag with customizable color."""
    name: str              # Tag name (e.g., "DEBUG", "INFO")
    color: str             # Hex color for tag text (e.g., "#00FFFF")
    enabled: bool = True   # Whether tag appears in filters
    order: int = 0         # Display order in UI
    message_color: str = "#FFFFFF"  # Hex color for message text (default white)
    message_match_tag: bool = False  # If True, message uses tag color
    show_count: bool = False  # If True, show entry count in filter UI

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "color": self.color,
            "enabled": self.enabled,
            "order": self.order,
            "message_color": self.message_color,
            "message_match_tag": self.message_match_tag,
            "show_count": self.show_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogTag':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            name=data["name"],
            color=data["color"],
            enabled=data.get("enabled", True),
            order=data.get("order", 0),
            message_color=data.get("message_color", "#FFFFFF"),
            message_match_tag=data.get("message_match_tag", False),
            show_count=data.get("show_count", False)
        )


@dataclass
class AppConfig:
    """Application configuration."""
    version: str = "1.2"
    last_directory: str = ""
    last_file: str = ""
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10
    tags: List[LogTag] = field(default_factory=list)
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    font_size: int = 9
    font_family: str = "Consolas"
    theme: str = "light"

    def __post_init__(self):
        """Initialize default tags if none provided."""
        if not self.tags:
            self.tags = self._default_tags()

    @staticmethod
    def _default_tags() -> List[LogTag]:
        """Return default log tags (v1.2: show_count for WARN/ERROR only)."""
        return [
            LogTag("DEBUG", "#00FFFF", True, 0, "#FFFFFF", False, False),   # Cyan tag, white message, no count
            LogTag("INFO", "#00FF00", True, 1, "#FFFFFF", False, False),    # Green tag, white message, no count
            LogTag("WARN", "#FFFF00", True, 2, "#FFFFFF", False, True),     # Yellow tag, white message, show count
            LogTag("ERROR", "#FF0000", True, 3, "#FFFFFF", False, True),    # Red tag, white message, show count
            LogTag("HEADER", "#0000FF", True, 4, "#FFFFFF", False, False),  # Blue tag, white message, no count
            LogTag("FOOTER", "#0000FF", True, 5, "#FFFFFF", False, False),  # Blue tag, white message, no count
        ]

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "version": self.version,
            "last_directory": self.last_directory,
            "last_file": self.last_file,
            "recent_files": self.recent_files,
            "max_recent_files": self.max_recent_files,
            "tags": [tag.to_dict() for tag in self.tags],
            "window": {
                "width": self.window_width,
                "height": self.window_height,
                "maximized": self.window_maximized
            },
            "preferences": {
                "font_size": self.font_size,
                "font_family": self.font_family,
                "theme": self.theme
            }
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from JSON dictionary."""
        tags = [LogTag.from_dict(tag_data) for tag_data in data.get("tags", [])]
        window = data.get("window", {})
        prefs = data.get("preferences", {})

        return cls(
            version=data.get("version", "1.2"),
            last_directory=data.get("last_directory", ""),
            last_file=data.get("last_file", ""),
            recent_files=data.get("recent_files", []),
            max_recent_files=data.get("max_recent_files", 10),
            tags=tags,
            window_width=window.get("width", 1200),
            window_height=window.get("height", 800),
            window_maximized=window.get("maximized", False),
            font_size=prefs.get("font_size", 9),
            font_family=prefs.get("font_family", "Consolas"),
            theme=prefs.get("theme", "light")
        )


class ConfigManager:
    """
    Manages application configuration persistence.

    Version 1.1: Uses JSON format (logreader_config.json)
    Automatically migrates from legacy text format (logreader_config.txt)
    """

    CONFIG_FILE_JSON = "logreader_config.json"
    CONFIG_FILE_TXT = "logreader_config.txt"  # Legacy format
    DEFAULT_FILE_PATH = "log.txt"

    _config: Optional[AppConfig] = None  # Cached config

    @classmethod
    def load_config(cls) -> AppConfig:
        """
        Load application configuration.

        Returns:
            AppConfig object with all settings

        Migration strategy:
        1. Check if JSON config exists → load it
        2. If not, check if old TXT config exists → migrate it
        3. If neither exists → create default config
        """
        # Return cached config if available
        if cls._config is not None:
            return cls._config

        json_path = Path(cls.CONFIG_FILE_JSON)
        txt_path = Path(cls.CONFIG_FILE_TXT)

        # Try to load JSON config
        if json_path.exists():
            try:
                with json_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if migration from v1.1 to v1.2 is needed
                if data.get("version") == "1.1":
                    logger.info("Migrating config from v1.1 to v1.2...")
                    data = cls._migrate_v1_1_to_v1_2(data)
                    cls._config = AppConfig.from_json(data)
                    cls.save_config(cls._config)  # Save migrated config
                    logger.info("Migration to v1.2 complete")
                else:
                    cls._config = AppConfig.from_json(data)
                    logger.info("Loaded configuration from JSON")

                return cls._config
            except Exception as e:
                logger.error(f"Error loading JSON config: {e}")
                # Fall through to migration or default

        # Try to migrate from old TXT format
        if txt_path.exists():
            logger.info("Found legacy config, migrating to JSON...")
            cls._config = cls._migrate_from_txt()
            if cls._config:
                # Save migrated config as JSON
                cls.save_config(cls._config)
                logger.info("Migration complete, saved as JSON")
                return cls._config

        # No config found, create default
        logger.info("No config found, creating default")
        cls._config = AppConfig()
        cls.save_config(cls._config)
        return cls._config

    @classmethod
    def save_config(cls, config: AppConfig) -> bool:
        """
        Save application configuration to JSON file.

        Args:
            config: AppConfig object to save

        Returns:
            True if save was successful, False otherwise
        """
        json_path = Path(cls.CONFIG_FILE_JSON)

        try:
            data = config.to_json()
            with json_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            cls._config = config  # Update cache
            logger.info(f"Saved configuration to {cls.CONFIG_FILE_JSON}")
            return True

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    @classmethod
    def _migrate_from_txt(cls) -> Optional[AppConfig]:
        """
        Migrate configuration from legacy text format to JSON.

        Legacy format:
        Line 1: last directory
        Line 2: last file path

        Returns:
            AppConfig with migrated data, or None on error
        """
        txt_path = Path(cls.CONFIG_FILE_TXT)

        try:
            with txt_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            config = AppConfig()  # Start with defaults

            # Parse legacy format
            if len(lines) >= 1:
                directory = lines[0].strip()
                if directory and Path(directory).exists():
                    config.last_directory = directory

            if len(lines) >= 2:
                file_path = lines[1].strip()
                if file_path and Path(file_path).exists():
                    config.last_file = file_path

            logger.info(f"Migrated config: directory={config.last_directory}, file={config.last_file}")
            return config

        except Exception as e:
            logger.error(f"Error migrating from TXT config: {e}")
            return None

    @classmethod
    def _migrate_v1_1_to_v1_2(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate configuration from v1.1 to v1.2.

        Changes in v1.2:
        - Added show_count field to LogTag (default: False for all tags except WARN/ERROR)

        Args:
            data: JSON data from v1.1 config

        Returns:
            Updated JSON data for v1.2
        """
        # Update version
        data["version"] = "1.2"

        # Add show_count field to all existing tags
        tags = data.get("tags", [])
        for tag in tags:
            # Default: only WARN and ERROR show counts
            tag_name = tag.get("name", "").upper()
            tag["show_count"] = (tag_name in ["WARN", "ERROR"])

        logger.info(f"Migrated {len(tags)} tags to v1.2 format")
        return data

    @classmethod
    def load_last_directory(cls) -> Optional[str]:
        """
        Load the last used directory from configuration.

        Returns:
            The last used directory if it exists, otherwise None.
        """
        config = cls.load_config()
        if config.last_directory and Path(config.last_directory).exists():
            return config.last_directory
        return None

    @classmethod
    def load_last_file_path(cls) -> str:
        """
        Load the last opened file path from configuration.

        Returns:
            The last opened file path if it exists and is valid,
            otherwise returns DEFAULT_FILE_PATH.
        """
        config = cls.load_config()
        if config.last_file and Path(config.last_file).exists():
            return config.last_file
        return cls.DEFAULT_FILE_PATH

    @classmethod
    def save_last_file_path(cls, file_path: str) -> bool:
        """
        Save the current file path and directory to configuration.

        Args:
            file_path: The file path to save

        Returns:
            True if save was successful, False otherwise
        """
        if not file_path:
            logger.warning("Attempted to save empty file path")
            return False

        config = cls.load_config()
        config.last_file = file_path
        config.last_directory = str(Path(file_path).parent)

        # Also add to recent files
        file_path_normalized = str(Path(file_path).resolve())
        if file_path_normalized in config.recent_files:
            config.recent_files.remove(file_path_normalized)
        config.recent_files.insert(0, file_path_normalized)
        config.recent_files = config.recent_files[:config.max_recent_files]

        return cls.save_config(config)

    @classmethod
    def load_tags(cls) -> List[LogTag]:
        """
        Load log tags from configuration.

        Returns:
            List of LogTag objects
        """
        config = cls.load_config()
        return config.tags

    @classmethod
    def save_tags(cls, tags: List[LogTag]) -> bool:
        """
        Save log tags to configuration.

        Args:
            tags: List of LogTag objects to save

        Returns:
            True if save was successful, False otherwise
        """
        config = cls.load_config()
        config.tags = tags
        return cls.save_config(config)

    @classmethod
    def add_tag(cls, tag: LogTag) -> bool:
        """
        Add a new tag to configuration.

        Args:
            tag: LogTag to add

        Returns:
            True if successful, False if tag name already exists
        """
        config = cls.load_config()

        # Check for duplicate names (case-insensitive)
        if any(t.name.upper() == tag.name.upper() for t in config.tags):
            logger.warning(f"Tag '{tag.name}' already exists")
            return False

        config.tags.append(tag)
        return cls.save_config(config)

    @classmethod
    def remove_tag(cls, tag_name: str) -> bool:
        """
        Remove a tag from configuration.

        Args:
            tag_name: Name of tag to remove

        Returns:
            True if successful, False if tag not found
        """
        config = cls.load_config()

        original_count = len(config.tags)
        config.tags = [t for t in config.tags if t.name.upper() != tag_name.upper()]

        if len(config.tags) == original_count:
            logger.warning(f"Tag '{tag_name}' not found")
            return False

        return cls.save_config(config)

    @classmethod
    def get_tag_color(cls, tag_name: str, default: str = "#808080") -> str:
        """
        Get color for a specific tag.

        Args:
            tag_name: Name of tag
            default: Default color if tag not found (gray)

        Returns:
            Hex color string
        """
        config = cls.load_config()

        for tag in config.tags:
            if tag.name.upper() == tag_name.upper():
                return tag.color

        return default

    @classmethod
    def get_or_create_tag(cls, tag_name: str) -> LogTag:
        """
        Get existing tag or create new one with default color.

        Args:
            tag_name: Name of tag

        Returns:
            LogTag object (existing or newly created)
        """
        config = cls.load_config()

        # Try to find existing tag
        for tag in config.tags:
            if tag.name.upper() == tag_name.upper():
                return tag

        # Create new tag with default gray color (no count display)
        new_tag = LogTag(
            name=tag_name.upper(),
            color="#808080",  # Gray tag
            enabled=True,
            order=len(config.tags),  # Append at end
            message_color="#FFFFFF",  # White message
            message_match_tag=False,
            show_count=False  # Auto-discovered tags don't show counts by default
        )

        config.tags.append(new_tag)
        cls.save_config(config)

        logger.info(f"Auto-created new tag: {tag_name}")
        return new_tag

    @classmethod
    def add_recent_file(cls, file_path: str) -> bool:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to add to recent files

        Returns:
            True if successful, False otherwise
        """
        if not file_path:
            return False

        config = cls.load_config()

        # Normalize path
        file_path = str(Path(file_path).resolve())

        # Remove if already in list (will re-add at top)
        if file_path in config.recent_files:
            config.recent_files.remove(file_path)

        # Add to front of list
        config.recent_files.insert(0, file_path)

        # Trim to max length
        config.recent_files = config.recent_files[:config.max_recent_files]

        return cls.save_config(config)

    @classmethod
    def get_recent_files(cls) -> List[str]:
        """
        Get list of recent files, filtered to only existing files.

        Returns:
            List of recent file paths that exist
        """
        config = cls.load_config()

        # Filter to only existing files
        existing_files = [f for f in config.recent_files if Path(f).exists()]

        # Update config if list changed
        if len(existing_files) != len(config.recent_files):
            config.recent_files = existing_files
            cls.save_config(config)

        return existing_files

    @classmethod
    def clear_recent_files(cls) -> bool:
        """
        Clear the recent files list.

        Returns:
            True if successful, False otherwise
        """
        config = cls.load_config()
        config.recent_files = []
        return cls.save_config(config)

    @classmethod
    def config_exists(cls) -> bool:
        """
        Check if any configuration file exists.

        Returns:
            True if JSON or TXT config exists, False otherwise
        """
        return Path(cls.CONFIG_FILE_JSON).exists() or Path(cls.CONFIG_FILE_TXT).exists()

    @classmethod
    def delete_config(cls) -> bool:
        """
        Delete the configuration file.

        Returns:
            True if deletion was successful, False on error

        Note:
            This is primarily useful for testing or resetting the application.
        """
        json_path = Path(cls.CONFIG_FILE_JSON)
        txt_path = Path(cls.CONFIG_FILE_TXT)

        try:
            if json_path.exists():
                json_path.unlink()
                logger.info("Deleted JSON config file")

            if txt_path.exists():
                txt_path.unlink()
                logger.info("Deleted TXT config file")

            cls._config = None  # Clear cache
            return True

        except Exception as e:
            logger.error(f"Error deleting config: {e}")
            return False

    @classmethod
    def reset_to_defaults(cls) -> bool:
        """
        Reset configuration to defaults.

        Returns:
            True if successful, False otherwise
        """
        cls._config = AppConfig()
        return cls.save_config(cls._config)
