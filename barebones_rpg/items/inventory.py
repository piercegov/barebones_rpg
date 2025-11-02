"""Inventory management system.

This module provides inventory functionality for managing collections of items.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .item import Item, ItemType, EquipSlot


class Inventory(BaseModel):
    """Inventory for storing items.

    Supports auto-stacking, slot limits, and weight limits.

    Example:
        >>> inv = Inventory(max_slots=20)
        >>> sword = create_weapon("Sword", atk=5)
        >>> inv.add_item(sword)
        >>> print(inv.count_items())
        1
    """

    max_slots: int = Field(default=20, description="Maximum number of item slots")
    max_weight: float = Field(default=-1, description="Max weight (-1 = unlimited)")
    items: List[Item] = Field(default_factory=list, description="Items in inventory")
    auto_stack: bool = Field(
        default=True, description="Automatically stack stackable items"
    )
    gold: int = Field(default=0, description="Gold/currency")

    model_config = {"arbitrary_types_allowed": True}

    def add_item(self, item: Item) -> bool:
        """Add an item to inventory.

        Args:
            item: Item to add

        Returns:
            True if item was added successfully
        """
        # Check weight limit
        if self.max_weight > 0:
            current_weight = self.get_total_weight()
            if current_weight + item.weight > self.max_weight:
                return False

        # Try to stack with existing items
        if self.auto_stack and item.stackable:
            for existing_item in self.items:
                if existing_item.can_stack_with(item):
                    overflow = existing_item.stack_with(item)
                    if overflow == 0:
                        return True
                    # Item was partially stacked, update quantity
                    item.quantity = overflow

        # Add as new item if there's space
        if len(self.items) < self.max_slots:
            self.items.append(item)
            return True

        return False

    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        """Remove an item from inventory.

        Args:
            item: Item to remove
            quantity: How many to remove

        Returns:
            True if item was removed
        """
        if item not in self.items:
            return False

        if item.stackable and item.quantity > quantity:
            item.quantity -= quantity
            return True
        elif item.quantity <= quantity:
            self.items.remove(item)
            return True

        return False

    def remove_item_by_name(self, item_name: str, quantity: int = 1) -> bool:
        """Remove an item by name.

        Args:
            item_name: Name of item to remove
            quantity: How many to remove

        Returns:
            True if item was removed
        """
        item = self.find_item(item_name)
        if item:
            return self.remove_item(item, quantity)
        return False

    def find_item(self, item_name: str) -> Optional[Item]:
        """Find an item by name.

        Args:
            item_name: Name of item to find

        Returns:
            Item if found, None otherwise
        """
        for item in self.items:
            if item.name == item_name:
                return item
        return None

    def find_items_by_type(self, item_type: ItemType) -> List[Item]:
        """Find all items of a specific type.

        Args:
            item_type: Type of items to find

        Returns:
            List of matching items
        """
        return [item for item in self.items if item.item_type == item_type]

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if inventory has an item.

        Args:
            item_name: Name of item
            quantity: Required quantity

        Returns:
            True if inventory has the item
        """
        item = self.find_item(item_name)
        return item is not None and item.quantity >= quantity

    def count_items(self) -> int:
        """Count total number of item slots used.

        Returns:
            Number of slots used
        """
        return len(self.items)

    def get_total_weight(self) -> float:
        """Calculate total weight of all items.

        Returns:
            Total weight
        """
        return sum(item.weight * item.quantity for item in self.items)

    def get_available_slots(self) -> int:
        """Get number of available slots.

        Returns:
            Number of free slots
        """
        return self.max_slots - len(self.items)

    def is_full(self) -> bool:
        """Check if inventory is full.

        Returns:
            True if inventory is full
        """
        return len(self.items) >= self.max_slots

    def sort_by_type(self) -> None:
        """Sort inventory by item type."""
        self.items.sort(key=lambda item: item.item_type.value)

    def sort_by_name(self) -> None:
        """Sort inventory by item name."""
        self.items.sort(key=lambda item: item.name)

    def sort_by_value(self) -> None:
        """Sort inventory by item value (descending)."""
        self.items.sort(key=lambda item: item.value, reverse=True)

    def add_gold(self, amount: int) -> None:
        """Add gold to inventory.

        Args:
            amount: Amount of gold to add
        """
        self.gold += amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold from inventory.

        Args:
            amount: Amount of gold to remove

        Returns:
            True if enough gold was available
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert inventory to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "max_slots": self.max_slots,
            "max_weight": self.max_weight,
            "gold": self.gold,
            "auto_stack": self.auto_stack,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inventory":
        """Create inventory from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Inventory instance
        """
        inventory = cls(
            max_slots=data.get("max_slots", 20),
            max_weight=data.get("max_weight", -1),
            auto_stack=data.get("auto_stack", True),
            gold=data.get("gold", 0),
        )

        # Load items
        for item_data in data.get("items", []):
            item = Item.from_dict(item_data)
            inventory.items.append(item)

        return inventory


class Equipment(BaseModel):
    """Equipment manager for equipped items.

    Manages which items are equipped in which slots.

    Example:
        >>> equipment = Equipment()
        >>> sword = create_weapon("Sword", atk=5)
        >>> equipment.equip(sword)
        >>> print(equipment.get_total_stat_bonus("atk"))
        5
    """

    slots: Dict[str, Optional[Item]] = Field(
        default_factory=lambda: {slot.value: None for slot in EquipSlot},  # type: ignore[arg-type]
        description="Equipment slots",
    )

    model_config = {"arbitrary_types_allowed": True}

    def equip(self, item: Item) -> Optional[Item]:
        """Equip an item.

        Args:
            item: Item to equip

        Returns:
            Previously equipped item in that slot (if any)
        """
        if item.equip_slot is None:
            return None

        slot = item.equip_slot.value
        old_item = self.slots.get(slot)
        self.slots[slot] = item
        return old_item

    def unequip(self, slot: EquipSlot) -> Optional[Item]:
        """Unequip an item from a slot.

        Args:
            slot: Slot to unequip from

        Returns:
            Unequipped item (if any)
        """
        slot_name = slot.value
        item = self.slots.get(slot_name)
        self.slots[slot_name] = None
        return item

    def get_equipped(self, slot: EquipSlot) -> Optional[Item]:
        """Get the item equipped in a slot.

        Args:
            slot: Slot to check

        Returns:
            Equipped item or None
        """
        return self.slots.get(slot.value)

    def get_all_equipped(self) -> List[Item]:
        """Get all equipped items.

        Returns:
            List of equipped items
        """
        return [item for item in self.slots.values() if item is not None]

    def get_total_stat_bonus(self, stat_name: str) -> int:
        """Calculate total stat bonus from all equipment.

        Args:
            stat_name: Name of the stat

        Returns:
            Total bonus from equipment
        """
        total = 0
        for item in self.get_all_equipped():
            if stat_name in item.stat_modifiers:
                total += item.stat_modifiers[stat_name]
        return total

    def get_all_stat_bonuses(self) -> Dict[str, int]:
        """Get all stat bonuses from equipment.

        Returns:
            Dictionary of stat bonuses
        """
        bonuses: Dict[str, int] = {}
        for item in self.get_all_equipped():
            for stat, value in item.stat_modifiers.items():
                bonuses[stat] = bonuses.get(stat, 0) + value
        return bonuses

    def is_slot_empty(self, slot: EquipSlot) -> bool:
        """Check if a slot is empty.

        Args:
            slot: Slot to check

        Returns:
            True if slot is empty
        """
        return self.slots.get(slot.value) is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert equipment to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "slots": {
                slot_name: item.to_dict() if item else None
                for slot_name, item in self.slots.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Equipment":
        """Create equipment from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Equipment instance
        """
        equipment = cls()

        # Load equipped items
        for slot_name, item_data in data.get("slots", {}).items():
            if item_data:
                item = Item.from_dict(item_data)
                equipment.slots[slot_name] = item

        return equipment
