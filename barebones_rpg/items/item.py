"""Item system for equipment, consumables, and quest items.

This module provides the base item system that can be extended for different
item types.
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum, auto
from uuid import uuid4
from pydantic import BaseModel, Field


class ItemType(Enum):
    """Types of items."""

    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()
    CONSUMABLE = auto()
    QUEST = auto()
    MATERIAL = auto()
    KEY = auto()
    MISC = auto()


class EquipSlot(Enum):
    """Equipment slots."""

    WEAPON = "weapon"
    HEAD = "head"
    BODY = "body"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    ACCESSORY_1 = "accessory_1"
    ACCESSORY_2 = "accessory_2"
    SHIELD = "shield"


class Item(BaseModel):
    """Base item class.

    All items in the game inherit from this class.

    Example:
        >>> sword = Item(
        ...     name="Iron Sword",
        ...     item_type=ItemType.WEAPON,
        ...     description="A basic iron sword",
        ...     stat_modifiers={"atk": 5}
        ... )
        >>> potion = Item(
        ...     name="Health Potion",
        ...     item_type=ItemType.CONSUMABLE,
        ...     on_use=lambda entity: entity.heal(50)
        ... )
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique item ID")
    name: str = Field(description="Item name")
    description: str = Field(default="", description="Item description")
    item_type: ItemType = Field(description="Type of item")

    # Properties
    value: int = Field(default=0, description="Gold value")
    weight: float = Field(default=1.0, description="Item weight")
    stackable: bool = Field(default=False, description="Can stack multiple items")
    max_stack: int = Field(default=1, description="Maximum stack size")
    quantity: int = Field(default=1, description="Current quantity in stack")

    # Equipment properties
    equip_slot: Optional[EquipSlot] = Field(default=None, description="Equipment slot")
    stat_modifiers: Dict[str, int] = Field(
        default_factory=dict, description="Stat modifications when equipped"
    )
    required_level: int = Field(default=1, description="Required level to use")

    # Weapon properties
    base_damage: int = Field(default=0, description="Base damage for weapons")
    damage_type: str = Field(
        default="physical", description="Damage type (physical, magic, or custom)"
    )

    # Consumable properties
    consumable: bool = Field(default=False, description="Item is consumed on use")
    on_use: Optional[Callable] = Field(
        default=None, description="Function called when item is used"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata"
    )

    model_config = {"arbitrary_types_allowed": True}

    def use(self, target: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Use the item.

        Args:
            target: Entity or object that the item is used on
            context: Additional context for item use

        Returns:
            Result of using the item
        """
        if self.on_use:
            result = self.on_use(target, context or {})
            if self.consumable and self.quantity > 0:
                self.quantity -= 1
            return result
        return None

    def can_stack_with(self, other: "Item") -> bool:
        """Check if this item can stack with another.

        Args:
            other: Another item

        Returns:
            True if items can stack
        """
        return (
            self.stackable
            and other.stackable
            and self.name == other.name
            and self.id != other.id  # Different instances
        )

    def stack_with(self, other: "Item") -> int:
        """Stack this item with another.

        Args:
            other: Another item to stack with

        Returns:
            Number of items that couldn't be stacked (overflow)
        """
        if not self.can_stack_with(other):
            return other.quantity

        available_space = self.max_stack - self.quantity
        if available_space >= other.quantity:
            self.quantity += other.quantity
            return 0
        else:
            self.quantity = self.max_stack
            return other.quantity - available_space

    def split(self, amount: int) -> Optional["Item"]:
        """Split a stack into two.

        Args:
            amount: Number of items to split off

        Returns:
            New item stack or None if can't split
        """
        if not self.stackable or amount >= self.quantity or amount <= 0:
            return None

        self.quantity -= amount
        new_item = self.model_copy(deep=True)
        new_item.id = str(uuid4())
        new_item.quantity = amount
        return new_item

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for saving.

        Returns:
            Dictionary representation
        """
        data = self.model_dump(exclude={"on_use"})
        if self.on_use:
            # Store reference to the function name if possible
            if hasattr(self.on_use, "__name__"):
                data["on_use_name"] = self.on_use.__name__
        return data


# Predefined item creation helpers


def create_weapon(
    name: str,
    base_damage: int,
    damage_type: str = "physical",
    description: str = "",
    value: int = 0,
    **kwargs,
) -> Item:
    """Create a weapon item.

    Args:
        name: Weapon name
        base_damage: Base damage dealt by weapon
        damage_type: Type of damage (physical, magic, or custom)
        description: Description
        value: Gold value
        **kwargs: Additional properties (stat_modifiers, metadata, etc.)

    Returns:
        Weapon item
    """
    return Item(
        name=name,
        description=description,
        item_type=ItemType.WEAPON,
        equip_slot=EquipSlot.WEAPON,
        base_damage=base_damage,
        damage_type=damage_type,
        value=value,
        **kwargs,
    )


def create_armor(
    name: str,
    physical_defense: int = 0,
    magic_defense: int = 0,
    slot: EquipSlot = EquipSlot.BODY,
    description: str = "",
    value: int = 0,
    **kwargs,
) -> Item:
    """Create an armor item.

    Args:
        name: Armor name
        physical_defense: Physical defense bonus
        magic_defense: Magic defense bonus
        slot: Equipment slot
        description: Description
        value: Gold value
        **kwargs: Additional properties

    Returns:
        Armor item
    """
    stat_modifiers = {}
    if physical_defense > 0:
        stat_modifiers["base_physical_defense"] = physical_defense
    if magic_defense > 0:
        stat_modifiers["base_magic_defense"] = magic_defense

    return Item(
        name=name,
        description=description,
        item_type=ItemType.ARMOR,
        equip_slot=slot,
        stat_modifiers=stat_modifiers,
        value=value,
        **kwargs,
    )


def create_consumable(
    name: str,
    on_use: Callable,
    description: str = "",
    value: int = 0,
    stackable: bool = True,
    max_stack: int = 99,
    **kwargs,
) -> Item:
    """Create a consumable item.

    Args:
        name: Item name
        on_use: Function to call when used
        description: Description
        value: Gold value
        stackable: Can stack
        max_stack: Max stack size
        **kwargs: Additional properties

    Returns:
        Consumable item
    """
    return Item(
        name=name,
        description=description,
        item_type=ItemType.CONSUMABLE,
        consumable=True,
        on_use=on_use,
        stackable=stackable,
        max_stack=max_stack,
        value=value,
        **kwargs,
    )


def create_quest_item(name: str, description: str = "", **kwargs) -> Item:
    """Create a quest item.

    Args:
        name: Item name
        description: Description
        **kwargs: Additional properties

    Returns:
        Quest item
    """
    return Item(
        name=name, description=description, item_type=ItemType.QUEST, value=0, **kwargs
    )
