"""Save manager for handling game save/load operations.

This module provides the SaveManager class for managing game saves,
including JSON serialization, file I/O, and directory management.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


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
        try:
            save_path = self._get_save_path(save_name)

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

        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load(self, save_name: str) -> Optional[Dict[str, Any]]:
        """Load game data from a file.

        Args:
            save_name: Name of the save to load

        Returns:
            Dictionary containing game state, or None if load failed

        Example:
            >>> data = manager.load("quicksave")
        """
        try:
            save_path = self._get_save_path(save_name)

            if not save_path.exists():
                print(f"Save file not found: {save_path}")
                return None

            with open(save_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)

            # Validate version (for now just warn)
            if full_data.get("version") != self.SAVE_VERSION:
                print(
                    f"Warning: Save file version mismatch. "
                    f"Expected {self.SAVE_VERSION}, got {full_data.get('version')}"
                )

            return full_data.get("data", {})

        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def delete(self, save_name: str) -> bool:
        """Delete a save file.

        Args:
            save_name: Name of the save to delete

        Returns:
            True if deletion was successful
        """
        try:
            save_path = self._get_save_path(save_name)
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False

    def list_saves(self) -> list[str]:
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
        except Exception as e:
            print(f"Error listing saves: {e}")
            return []

    def get_save_info(self, save_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a save file.

        Args:
            save_name: Name of the save

        Returns:
            Dictionary with save metadata (version, timestamp, etc.)
        """
        try:
            save_path = self._get_save_path(save_name)

            if not save_path.exists():
                return None

            with open(save_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)

            return {
                "version": full_data.get("version"),
                "timestamp": full_data.get("timestamp"),
                "save_name": full_data.get("save_name"),
                "file_size": save_path.stat().st_size,
            }

        except Exception as e:
            print(f"Error getting save info: {e}")
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
