"""
Configuration management for LogReader application.

This module handles loading and saving application configuration,
such as the last opened file path.
"""

from pathlib import Path
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration persistence.

    The configuration is stored in a simple text file in the working directory.
    Format: Two lines - first line is last directory, second line is last file path.
    """

    CONFIG_FILE = "logreader_config.txt"
    DEFAULT_FILE_PATH = "log.txt"

    @classmethod
    def load_last_directory(cls) -> Optional[str]:
        """
        Load the last used directory from configuration.

        Returns:
            The last used directory if it exists, otherwise None.
        """
        config_path = Path(cls.CONFIG_FILE)

        try:
            if not config_path.exists():
                logger.debug(f"Config file not found: {cls.CONFIG_FILE}")
                return None

            with config_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                return None

            directory = lines[0].strip()

            if directory and Path(directory).exists():
                logger.info(f"Loaded last directory: {directory}")
                return directory

            # Fallback: try to extract directory from file path (old format)
            if directory and not Path(directory).exists():
                parent = str(Path(directory).parent)
                if Path(parent).exists():
                    return parent

            return None

        except Exception as e:
            logger.error(f"Error loading last directory: {e}")
            return None

    @classmethod
    def load_last_file_path(cls) -> str:
        """
        Load the last opened file path from configuration.

        Returns:
            The last opened file path if it exists and is valid,
            otherwise returns DEFAULT_FILE_PATH.
        """
        config_path = Path(cls.CONFIG_FILE)

        try:
            if not config_path.exists():
                logger.debug(f"Config file not found: {cls.CONFIG_FILE}")
                return cls.DEFAULT_FILE_PATH

            with config_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                logger.debug("Config file is empty")
                return cls.DEFAULT_FILE_PATH

            # New format: second line is file path
            if len(lines) >= 2:
                file_path = lines[1].strip()
            else:
                # Old format: single line is file path
                file_path = lines[0].strip()

            if not file_path:
                logger.debug("No file path in config")
                return cls.DEFAULT_FILE_PATH

            # Check if the file still exists
            if Path(file_path).exists():
                logger.info(f"Loaded last file path: {file_path}")
                return file_path
            else:
                logger.warning(f"Last file path no longer exists: {file_path}")
                return cls.DEFAULT_FILE_PATH

        except Exception as e:
            logger.error(f"Error loading config: {e}")
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

        config_path = Path(cls.CONFIG_FILE)

        try:
            # Extract directory from file path
            directory = str(Path(file_path).parent)

            # Write both directory and file path
            with config_path.open('w', encoding='utf-8') as f:
                f.write(f"{directory}\n")
                f.write(f"{file_path}\n")

            logger.info(f"Saved directory: {directory}, file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    @classmethod
    def config_exists(cls) -> bool:
        """
        Check if the configuration file exists.

        Returns:
            True if config file exists, False otherwise
        """
        return Path(cls.CONFIG_FILE).exists()

    @classmethod
    def delete_config(cls) -> bool:
        """
        Delete the configuration file.

        Returns:
            True if deletion was successful or file didn't exist, False on error

        Note:
            This is primarily useful for testing or resetting the application.
        """
        config_path = Path(cls.CONFIG_FILE)

        try:
            if config_path.exists():
                config_path.unlink()
                logger.info("Deleted config file")
            return True

        except Exception as e:
            logger.error(f"Error deleting config: {e}")
            return False
