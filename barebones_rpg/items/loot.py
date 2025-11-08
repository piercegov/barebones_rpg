"""Loot drop system for handling item drops from enemies and containers.

This module provides functionality for rolling on loot tables and managing
dropped items.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import random

from .item import Item
from .loot_manager import LootManager


@dataclass
class LootDrop:
    """Represents an item that has been dropped.

    Example:
        >>> from barebones_rpg.items import LootDrop, create_material
        >>> bone = create_material("Bone", value=5)
        >>> drop = LootDrop(item=bone, source=goblin, quantity=1)
    """

    item: Item
    """The dropped Item instance"""
    source: Optional[Any] = None
    """Entity or object that dropped the item (optional)"""
    quantity: int = 1
    """Number of items dropped (for stackable items)"""


def roll_loot_table(
    loot_table: List[Dict[str, Any]], source: Optional[Any] = None
) -> List[LootDrop]:
    """Roll on a loot table to determine which items drop.

    The loot table should be a list of dictionaries with the following format::

        [
            {"item": "Goblin Bone", "chance": 0.3},  # 30% drop chance, lookup by name
            {"item": bone_item, "chance": 0.5},      # 50% drop chance, direct Item object
            {"item": "Rare Gem", "chance": 0.05}     # 5% drop chance
        ]

    For string item names, the LootManager is used to retrieve the item template.
    For Item objects, a deep copy is created. Each entry is rolled independently,
    so multiple items can drop from a single table.

    Args:
        loot_table: List of loot entries with "item" and "chance" keys
        source: Optional entity/object that is dropping the loot

    Returns:
        List of LootDrop objects for items that successfully dropped

    Example:
        >>> from barebones_rpg.items import roll_loot_table, LootManager, create_material
        >>>
        >>> # Setup manager
        >>> LootManager().register("Bone", create_material("Bone", value=5))
        >>>
        >>> # Define loot table
        >>> loot_table = [
        ...     {"item": "Bone", "chance": 0.5},
        ...     {"item": create_material("Scale", value=10), "chance": 0.1}
        ... ]
        >>>
        >>> # Roll for loot
        >>> drops = roll_loot_table(loot_table, source=goblin)
        >>> for drop in drops:
        ...     print(f"Dropped: {drop.item.name}")
    """
    drops: List[LootDrop] = []

    for entry in loot_table:
        # Validate entry format
        if not isinstance(entry, dict):
            continue

        if "item" not in entry or "chance" not in entry:
            continue

        item_ref = entry["item"]
        chance = entry["chance"]

        # Validate chance is a number between 0 and 1
        try:
            chance = float(chance)
            if chance < 0 or chance > 1:
                continue
        except (TypeError, ValueError):
            continue

        # Roll for this item
        if random.random() > chance:
            continue

        # Get the item
        item: Optional[Item] = None

        if isinstance(item_ref, str):
            # Look up in manager
            item = LootManager().get(item_ref)
            if item is None:
                # Item not found in manager, skip
                continue
        elif isinstance(item_ref, Item):
            # Direct item object - make a deep copy and generate new ID
            from uuid import uuid4

            item = item_ref.model_copy(deep=True)
            item.id = str(uuid4())  # Generate new ID for the copy
        else:
            # Unknown item reference type
            continue

        # Determine quantity (support optional "quantity" or "min_quantity"/"max_quantity")
        quantity = 1
        if "quantity" in entry:
            try:
                quantity = int(entry["quantity"])
            except (TypeError, ValueError):
                quantity = 1
        elif "min_quantity" in entry and "max_quantity" in entry:
            try:
                min_qty = int(entry["min_quantity"])
                max_qty = int(entry["max_quantity"])
                quantity = random.randint(min_qty, max_qty)
            except (TypeError, ValueError):
                quantity = 1

        # Update item quantity if stackable
        if item.stackable and quantity > 1:
            item.quantity = min(quantity, item.max_stack)

        # Create drop
        drops.append(LootDrop(item=item, source=source, quantity=quantity))

    return drops


def create_loot_entry(
    item: Union[str, Item], chance: float, quantity: int = 1
) -> Dict[str, Any]:
    """Helper function to create a loot table entry.

    Args:
        item: Item name (string) or Item object
        chance: Drop chance (0.0 to 1.0)
        quantity: Number of items to drop (default: 1)

    Returns:
        Dictionary formatted for use in loot tables

    Example:
        >>> entry = create_loot_entry("Goblin Bone", 0.3)
        >>> entry2 = create_loot_entry(rare_item, 0.05, quantity=3)
        >>> loot_table = [entry, entry2]
    """
    return {"item": item, "chance": chance, "quantity": quantity}
