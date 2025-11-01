"""Global loot registry for managing item drops.

This module provides a global registry for mapping item names to item templates
or factory functions, enabling both data-driven and code-first loot systems.
"""

from typing import Optional, Callable, Union, Dict, Set
from .item import Item


class LootRegistry:
    """Global registry for loot items.
    
    The LootRegistry allows registering item templates or factory functions
    that can be referenced by name in loot tables. It supports both static
    items (templates that get deep copied) and dynamic items (factory functions).
    
    It also tracks unique items to ensure they only drop once per game.
    
    Example:
        >>> from barebones_rpg.items import LootRegistry, create_material, Item
        >>> 
        >>> # Register a static template
        >>> bone = create_material("Goblin Bone", value=5)
        >>> LootRegistry.register("Goblin Bone", bone)
        >>> 
        >>> # Register a factory function
        >>> def random_potion():
        ...     import random
        ...     healing = random.randint(30, 50)
        ...     return create_consumable(f"Potion ({healing}hp)", 
        ...                             on_use=lambda t, c: t.heal(healing))
        >>> LootRegistry.register("Random Potion", random_potion)
        >>> 
        >>> # Get items (creates new instances)
        >>> item1 = LootRegistry.get("Goblin Bone")
        >>> item2 = LootRegistry.get("Goblin Bone")
        >>> assert item1.id != item2.id  # Different instances
    """
    
    _registry: Dict[str, Union[Item, Callable[[], Item]]] = {}
    _dropped_uniques: Set[str] = set()
    
    @classmethod
    def register(
        cls, 
        name: str, 
        item_or_factory: Union[Item, Callable[[], Optional[Item]]]
    ) -> None:
        """Register an item template or factory function.
        
        Args:
            name: Name to register the item under
            item_or_factory: Either an Item instance (will be deep copied when retrieved)
                           or a callable that returns an Item or None
        
        Example:
            >>> LootRegistry.register("Gold Coin", create_material("Gold Coin", value=1))
            >>> LootRegistry.register("Random Weapon", lambda: create_weapon(...))
        """
        cls._registry[name] = item_or_factory
    
    @classmethod
    def get(cls, name: str) -> Optional[Item]:
        """Get an item by name, creating a new instance.
        
        For item templates, creates a deep copy. For factory functions, calls
        the function. Tracks unique items and returns None if a unique item
        has already been dropped.
        
        Args:
            name: Name of the item to retrieve
            
        Returns:
            New Item instance, or None if not found or unique already dropped
            
        Example:
            >>> item = LootRegistry.get("Goblin Bone")
            >>> if item:
            ...     player.inventory.add_item(item)
        """
        if name not in cls._registry:
            return None
        
        template_or_factory = cls._registry[name]
        
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
            if name in cls._dropped_uniques:
                return None
            cls._dropped_uniques.add(name)
        
        return item
    
    @classmethod
    def has(cls, name: str) -> bool:
        """Check if an item is registered.
        
        Args:
            name: Name of the item
            
        Returns:
            True if item is registered
            
        Example:
            >>> if LootRegistry.has("Goblin Bone"):
            ...     print("Item is registered")
        """
        return name in cls._registry
    
    @classmethod
    def clear(cls) -> None:
        """Clear the entire registry.
        
        This removes all registered items and resets unique item tracking.
        Useful for testing or resetting game state.
        
        Example:
            >>> LootRegistry.clear()  # Start fresh
        """
        cls._registry.clear()
        cls._dropped_uniques.clear()
    
    @classmethod
    def reset_unique_tracking(cls) -> None:
        """Reset unique item tracking without clearing the registry.
        
        This allows unique items to drop again without re-registering them.
        Useful for new game+ or testing.
        
        Example:
            >>> LootRegistry.reset_unique_tracking()
        """
        cls._dropped_uniques.clear()

