"""Global loot manager for managing item drops.

This module provides a singleton manager for mapping item names to item templates
or factory functions, enabling both data-driven and code-first loot systems.
"""

from typing import Optional, Callable, Union, Dict, Set, Any
from ..core.singleton import Singleton
from .item import Item


class LootManager(metaclass=Singleton):
    """Global manager for loot items (Singleton).

    The LootManager allows registering item templates or factory functions
    that can be referenced by name in loot tables. It supports both static
    items (templates that get deep copied) and dynamic items (factory functions).

    It also tracks unique items to ensure they only drop once per game.

    Example:
        >>> from barebones_rpg.items import LootManager, create_material, Item
        >>>
        >>> # Register a static template
        >>> bone = create_material("Goblin Bone", value=5)
        >>> LootManager().register("Goblin Bone", bone)
        >>>
        >>> # Register a factory function
        >>> def random_potion():
        ...     import random
        ...     healing = random.randint(30, 50)
        ...     return create_consumable(f"Potion ({healing}hp)",
        ...                             on_use=lambda t, c: t.heal(healing))
        >>> LootManager().register("Random Potion", random_potion)
        >>>
        >>> # Get items (creates new instances)
        >>> item1 = LootManager().get("Goblin Bone")
        >>> item2 = LootManager().get("Goblin Bone")
        >>> assert item1.id != item2.id  # Different instances
    """

    def __init__(self):
        """Initialize the loot manager."""
        self._registry: Dict[str, Union[Item, Callable[[], Optional[Item]]]] = {}
        self._dropped_uniques: Set[str] = set()

    def register(
        self, name: str, item_or_factory: Union[Item, Callable[[], Optional[Item]]]
    ) -> None:
        """Register an item template or factory function.

        Automatically registers any callbacks (on_use) to the CallbackRegistry
        for serialization support.

        Args:
            name: Name to register the item under
            item_or_factory: Either an Item instance (will be deep copied when retrieved)
                           or a callable that returns an Item or None

        Example:
            >>> LootManager().register("Gold Coin", create_material("Gold Coin", value=1))
            >>> LootManager().register("Random Weapon", lambda: create_weapon(...))
        """
        from ..core.serialization import CallbackRegistry

        # Auto-register callbacks for Item instances
        if isinstance(item_or_factory, Item):
            if item_or_factory.on_use:
                CallbackRegistry.register(f"{name}.on_use", item_or_factory.on_use)

        self._registry[name] = item_or_factory

    def get(self, name: str) -> Optional[Item]:
        """Get an item by name, creating a new instance.

        For item templates, creates a deep copy. For factory functions, calls
        the function. Tracks unique items and returns None if a unique item
        has already been dropped.

        Args:
            name: Name of the item to retrieve

        Returns:
            New Item instance, or None if not found or unique already dropped

        Example:
            >>> item = LootManager().get("Goblin Bone")
            >>> if item:
            ...     player.inventory.add_item(item)
        """
        if name not in self._registry:
            return None

        template_or_factory = self._registry[name]

        # Call factory function
        if callable(template_or_factory):
            item = template_or_factory()
            if item is None:
                return None
        else:
            # Deep copy the template and generate new ID
            from uuid import uuid4

            item = template_or_factory.model_copy(deep=True)
            item.id = str(uuid4())  # Generate new ID for the copy

        # Check if item is unique and already dropped
        if item.unique:
            if name in self._dropped_uniques:
                return None
            self._dropped_uniques.add(name)

        return item

    def has(self, name: str) -> bool:
        """Check if an item is registered.

        Args:
            name: Name of the item

        Returns:
            True if item is registered

        Example:
            >>> if LootManager().has("Goblin Bone"):
            ...     print("Item is registered")
        """
        return name in self._registry

    def clear(self) -> None:
        """Clear the entire manager.

        This removes all registered items and resets unique item tracking.
        Useful for testing or resetting game state.

        Example:
            >>> LootManager().clear()  # Start fresh
        """
        self._registry.clear()
        self._dropped_uniques.clear()

    def reset_unique_tracking(self) -> None:
        """Reset unique item tracking without clearing the registry.

        This allows unique items to drop again without re-registering them.
        Useful for new game+ or testing.

        Example:
            >>> LootManager().reset_unique_tracking()
        """
        self._dropped_uniques.clear()

    def save(self) -> Dict[str, Any]:
        """Save manager state.

        Returns:
            Dictionary with dropped unique items
        """
        return {"dropped_uniques": list(self._dropped_uniques)}

    def load(self, data: Dict[str, Any]) -> None:
        """Load manager state.

        Args:
            data: Saved data containing dropped unique items
        """
        self._dropped_uniques = set(data.get("dropped_uniques", []))

    @classmethod
    def reset(cls) -> None:
        """Reset manager to initial state (for testing).

        Clears the singleton instance, causing the next access to create
        a fresh instance with default initialization.
        """
        if cls in Singleton._instances:
            del Singleton._instances[cls]
