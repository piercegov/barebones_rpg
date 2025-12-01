"""Save manager for handling game save/load operations.

This module provides the SaveManager class for managing game saves,
including JSON serialization, file I/O, and directory management.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from .exceptions import SerializationError

logger = logging.getLogger(__name__)


class SaveManager:
    """Manager for saving and loading game state.

    Handles JSON serialization, file I/O, directory creation, and versioning.

    Example:
        >>> manager = SaveManager("saves")
        >>> save_data = {"player": {"name": "Hero", "level": 5}}
        >>> manager.save("my_save", save_data)
        >>> loaded = manager.load("my_save")
        >>> print(loaded["player"]["name"])
        Hero
    """

    SAVE_VERSION = "1.0.0"

    def __init__(self, save_directory: str):
        """Initialize the save manager.

        Args:
            save_directory: Directory path for save files (absolute or relative)
        """
        self.save_directory = Path(save_directory).resolve()
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create the save directory if it doesn't exist."""
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def _get_save_path(self, save_name: str) -> Path:
        """Get the full path for a save file.

        Args:
            save_name: Name of the save

        Returns:
            Path to the save file
        """
        # Sanitize save name
        safe_name = "".join(c for c in save_name if c.isalnum() or c in ("-", "_"))
        return self.save_directory / f"{safe_name}.json"

    def save(self, save_name: str, save_data: Dict[str, Any]) -> bool:
        """Save game data to a file.

        Args:
            save_name: Name of the save
            save_data: Dictionary containing game state

        Returns:
            True if save was successful

        Example:
            >>> manager.save("quicksave", game_state)
        """
        save_path = self._get_save_path(save_name)
        try:
            # Add metadata
            full_data = {
                "version": self.SAVE_VERSION,
                "timestamp": datetime.now().isoformat(),
                "save_name": save_name,
                "data": save_data,
            }

            # Write to file with pretty formatting
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)

            return True

        except PermissionError as e:
            logger.error(f"Permission denied saving to {save_path}: {e}")
            raise SerializationError(
                f"Permission denied: cannot write to {save_path}"
            ) from e
        except TypeError as e:
            logger.error(f"Data not JSON serializable: {e}")
            raise SerializationError(
                f"Save data contains non-serializable objects: {e}"
            ) from e
        except OSError as e:
            logger.error(f"OS error saving game: {e}")
            raise SerializationError(f"Failed to save game: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error saving game: {e}")
            raise SerializationError(f"Unexpected error saving game: {e}") from e

    def load(self, save_name: str) -> Optional[Dict[str, Any]]:
        """Load game data from a file.

        Args:
            save_name: Name of the save to load

        Returns:
            Dictionary containing game state, or None if load failed

        Example:
            >>> data = manager.load("quicksave")
        """
        save_path = self._get_save_path(save_name)

        if not save_path.exists():
            logger.warning(f"Save file not found: {save_path}")
            return None

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)

            # Validate version (for now just warn)
            if full_data.get("version") != self.SAVE_VERSION:
                logger.warning(
                    f"Save file version mismatch. "
                    f"Expected {self.SAVE_VERSION}, got {full_data.get('version')}"
                )

            return full_data.get("data", {})

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted save file {save_path}: {e}")
            raise SerializationError(
                f"Save file is corrupted or invalid JSON: {e}"
            ) from e
        except PermissionError as e:
            logger.error(f"Permission denied reading {save_path}: {e}")
            raise SerializationError(
                f"Permission denied: cannot read {save_path}"
            ) from e
        except OSError as e:
            logger.error(f"OS error loading game: {e}")
            raise SerializationError(f"Failed to load game: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading game: {e}")
            raise SerializationError(f"Unexpected error loading game: {e}") from e

    def delete(self, save_name: str) -> bool:
        """Delete a save file.

        Args:
            save_name: Name of the save to delete

        Returns:
            True if deletion was successful
        """
        save_path = self._get_save_path(save_name)
        try:
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except PermissionError as e:
            logger.error(f"Permission denied deleting {save_path}: {e}")
            return False
        except OSError as e:
            logger.error(f"Error deleting save {save_path}: {e}")
            return False

    def list_saves(self) -> List[str]:
        """List all available save files.

        Returns:
            List of save names

        Example:
            >>> saves = manager.list_saves()
            >>> print(saves)
            ['quicksave', 'autosave', 'manual_save_1']
        """
        try:
            saves = []
            for file_path in self.save_directory.glob("*.json"):
                # Remove .json extension
                save_name = file_path.stem
                saves.append(save_name)
            return sorted(saves)
        except PermissionError as e:
            logger.error(f"Permission denied accessing save directory: {e}")
            return []
        except OSError as e:
            logger.error(f"Error listing saves: {e}")
            return []

    def get_save_info(self, save_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a save file.

        Args:
            save_name: Name of the save

        Returns:
            Dictionary with save metadata (version, timestamp, etc.)
        """
        save_path = self._get_save_path(save_name)

        if not save_path.exists():
            return None

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)

            return {
                "version": full_data.get("version"),
                "timestamp": full_data.get("timestamp"),
                "save_name": full_data.get("save_name"),
                "file_size": save_path.stat().st_size,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted save file {save_path}: {e}")
            return None
        except PermissionError as e:
            logger.error(f"Permission denied reading {save_path}: {e}")
            return None
        except OSError as e:
            logger.error(f"Error reading save info from {save_path}: {e}")
            return None

    def exists(self, save_name: str) -> bool:
        """Check if a save file exists.

        Args:
            save_name: Name of the save

        Returns:
            True if save exists
        """
        save_path = self._get_save_path(save_name)
        return save_path.exists()
