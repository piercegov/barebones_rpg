"""Generic registry base class for framework registries.

This module provides a reusable registry pattern used throughout the framework
for managing collections of named objects (AI types, loot items, callbacks, etc.).
"""

from typing import TypeVar, Generic, Dict, Optional, List

T = TypeVar("T")


class Registry(Generic[T]):
    """Base class for type-safe registries.

    Provides a common interface for registering and retrieving named objects.
    Subclasses should define their own _registry class variable to maintain
    separate storage.

    Example:
        >>> class MyItemRegistry(Registry[Item]):
        ...     _registry: Dict[str, Item] = {}
        >>>
        >>> item = Item(name="Sword")
        >>> MyItemRegistry.register("sword", item)
        >>> retrieved = MyItemRegistry.get("sword")
        >>> assert retrieved is item
    """

    _registry: Dict[str, T] = {}

    @classmethod
    def register(cls, name: str, item: T) -> None:
        """Register an item with a name.

        Args:
            name: Unique name for the item
            item: Item to register

        Example:
            >>> Registry.register("my_item", my_item)
        """
        cls._registry[name] = item

    @classmethod
    def get(cls, name: str) -> Optional[T]:
        """Get an item by name.

        Args:
            name: Name of the item to retrieve

        Returns:
            The registered item or None if not found

        Example:
            >>> item = Registry.get("my_item")
        """
        return cls._registry.get(name)

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if an item is registered.

        Args:
            name: Name to check

        Returns:
            True if the item is registered

        Example:
            >>> if Registry.has("my_item"):
            ...     print("Item exists")
        """
        return name in cls._registry

    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get all registered names.

        Returns:
            List of all registered names

        Example:
            >>> names = Registry.get_all_names()
            >>> print(names)
            ['item1', 'item2', 'item3']
        """
        return list(cls._registry.keys())

    @classmethod
    def get_all(cls) -> Dict[str, T]:
        """Get all registered items.

        Returns:
            Dictionary of all registered items

        Example:
            >>> items = Registry.get_all()
            >>> for name, item in items.items():
            ...     print(f"{name}: {item}")
        """
        return dict(cls._registry)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered items.

        This is primarily for testing purposes.

        Example:
            >>> Registry.clear()
        """
        cls._registry.clear()
