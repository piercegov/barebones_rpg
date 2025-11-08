"""Damage type system with manager for flexible damage types and resistances.

This module provides a singleton manager for damage types, allowing games to
register custom damage types with metadata while maintaining flexibility.
"""

from typing import Dict, Any, Optional, List
import warnings
from pydantic import BaseModel, Field
from ..core.singleton import Singleton


class DamageTypeMetadata(BaseModel):
    """Metadata for a damage type."""

    name: str = Field(description="Damage type name")
    color: Optional[str] = Field(default=None, description="Display color (for UI)")
    description: Optional[str] = Field(
        default=None, description="Human-readable description"
    )
    tags: List[str] = Field(
        default_factory=list, description="Additional classification tags"
    )
    custom: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata fields"
    )

    model_config = {"extra": "allow"}  # Allow additional fields


class DamageTypeManager(metaclass=Singleton):
    """Global manager for damage types (Singleton).

    This manager handles all damage types in the game. It supports:
    - Pre-registration of common types
    - Metadata attachment (colors, descriptions, tags)
    - Lenient mode (auto-registers unknown types)
    - Query capabilities

    Example:
        >>> # Register a custom damage type
        >>> DamageTypeManager().register("necrotic", color="green", description="Death magic")
        >>>
        >>> # Check if registered
        >>> DamageTypeManager().is_registered("necrotic")
        True
        >>>
        >>> # Get metadata
        >>> meta = DamageTypeManager().get_metadata("necrotic")
        >>> print(meta.color)
        green
        >>>
        >>> # Get all registered types
        >>> types = DamageTypeManager().get_all()
        >>> print(types)
        ['physical', 'magic', 'fire', 'ice', 'poison', 'lightning', 'dark', 'holy', 'necrotic']
    """

    def __init__(self):
        """Initialize the registry with common damage types."""
        self._types: Dict[str, DamageTypeMetadata] = {}
        self._lenient_mode = True
        self._warned_types: set = set()

        # Pre-register common damage types (using instance method)
        self._register_instance(
            "physical",
            color="gray",
            description="Physical damage from weapons and physical attacks",
        )
        self._register_instance(
            "magic", color="blue", description="Generic magical damage"
        )
        self._register_instance(
            "fire",
            color="red",
            description="Fire damage that burns targets",
            tags=["elemental"],
        )
        self._register_instance(
            "ice",
            color="cyan",
            description="Ice damage that freezes targets",
            tags=["elemental"],
        )
        self._register_instance(
            "poison",
            color="green",
            description="Poison damage that can afflict over time",
            tags=["status"],
        )
        self._register_instance(
            "lightning",
            color="yellow",
            description="Lightning damage that electrifies targets",
            tags=["elemental"],
        )
        self._register_instance(
            "dark",
            color="purple",
            description="Dark/shadow damage",
            tags=["arcane"],
        )
        self._register_instance(
            "holy",
            color="gold",
            description="Holy/light damage",
            tags=["arcane"],
        )

    def _register_instance(
        self,
        damage_type: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Internal instance method for registration (avoids singleton recursion).

        Args:
            damage_type: Name of the damage type
            color: Display color
            description: Description
            tags: Classification tags
            **kwargs: Custom metadata
        """
        metadata = DamageTypeMetadata(
            name=damage_type,
            color=color,
            description=description,
            tags=tags or [],
            custom=kwargs,
        )
        self._types[damage_type] = metadata

    def register(
        self,
        damage_type: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Register a damage type with optional metadata.

        Args:
            damage_type: Name of the damage type (e.g., "fire", "necrotic")
            color: Display color for UI
            description: Human-readable description
            tags: List of classification tags
            **kwargs: Additional custom metadata
        """
        self._register_instance(damage_type, color, description, tags, **kwargs)

    def is_registered(self, damage_type: str) -> bool:
        """Check if a damage type is registered.

        Args:
            damage_type: Name of the damage type

        Returns:
            True if registered
        """
        return damage_type in self._types

    def get_metadata(self, damage_type: str) -> Optional[DamageTypeMetadata]:
        """Get metadata for a damage type.

        Args:
            damage_type: Name of the damage type

        Returns:
            Metadata object or None if not registered
        """
        return self._types.get(damage_type)

    def get_all(self) -> List[str]:
        """Get all registered damage types.

        Returns:
            List of damage type names
        """
        return list(self._types.keys())

    def get_all_with_metadata(self) -> Dict[str, DamageTypeMetadata]:
        """Get all damage types with their metadata.

        Returns:
            Dictionary mapping damage type names to metadata
        """
        return dict(self._types)

    def ensure_registered(self, damage_type: str) -> None:
        """Ensure a damage type is registered, auto-registering if in lenient mode.

        This is called internally when an unknown damage type is encountered.
        In lenient mode, it auto-registers with a warning. In strict mode,
        it raises an error.

        Args:
            damage_type: Name of the damage type

        Raises:
            ValueError: If damage type not registered and not in lenient mode
        """
        if self.is_registered(damage_type):
            return

        if self._lenient_mode:
            # Auto-register with warning (only warn once per type)
            if damage_type not in self._warned_types:
                warnings.warn(
                    f"Damage type '{damage_type}' not registered. Auto-registering in lenient mode. "
                    f"Consider pre-registering with DamageTypeManager().register('{damage_type}', ...)",
                    UserWarning,
                    stacklevel=3,
                )
                self._warned_types.add(damage_type)

            self.register(damage_type, description="Auto-registered damage type")
        else:
            raise ValueError(
                f"Damage type '{damage_type}' not registered. "
                f"Register it with DamageTypeManager().register('{damage_type}', ...)"
            )

    def set_lenient_mode(self, lenient: bool) -> None:
        """Set lenient mode on/off.

        In lenient mode, unknown damage types are auto-registered with a warning.
        In strict mode, unknown damage types raise an error.

        Args:
            lenient: True for lenient mode, False for strict mode
        """
        self._lenient_mode = lenient

    @classmethod
    def reset(cls) -> None:
        """Reset manager to initial state (for testing).

        Clears the singleton instance, causing the next access to create
        a fresh instance with default initialization.
        """
        if cls in Singleton._instances:
            del Singleton._instances[cls]
