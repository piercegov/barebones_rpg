"""Tests for the inventory system."""

import pytest
from barebones_rpg.items.item import (
    Item,
    ItemType,
    EquipSlot,
    create_weapon,
    create_armor,
)
from barebones_rpg.items.inventory import Inventory, Equipment


def test_adding_item_when_inventory_full():
    """Adding an item when inventory is full should return False."""
    inventory = Inventory(max_slots=2)

    item1 = Item(name="Sword", item_type=ItemType.WEAPON)
    item2 = Item(name="Shield", item_type=ItemType.ARMOR)
    item3 = Item(name="Potion", item_type=ItemType.CONSUMABLE)

    assert inventory.add_item(item1) is True
    assert inventory.add_item(item2) is True
    assert inventory.add_item(item3) is False


def test_weight_limit_prevents_adding_items():
    """Weight limit should prevent adding items that would exceed max_weight."""
    inventory = Inventory(max_slots=10, max_weight=10.0)

    heavy_item1 = Item(name="Heavy Armor", item_type=ItemType.ARMOR, weight=6.0)
    heavy_item2 = Item(name="Heavy Sword", item_type=ItemType.WEAPON, weight=5.0)

    assert inventory.add_item(heavy_item1) is True
    assert inventory.add_item(heavy_item2) is False


def test_auto_stacking_with_partial_overflow():
    """Auto-stacking should handle partial overflow correctly."""
    inventory = Inventory(max_slots=5, auto_stack=True)

    potions1 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=8,
    )
    potions2 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=5,
    )

    inventory.add_item(potions1)
    result = inventory.add_item(potions2)

    assert result is True
    assert potions1.quantity == 10
    assert potions2.quantity == 3
    assert len(inventory.items) == 2


def test_equipment_stat_bonuses_sum_correctly():
    """Equipment stat bonuses should sum correctly across multiple items."""
    equipment = Equipment()

    # Weapons no longer provide atk stat bonuses, they have base_damage instead
    # Give sword a strength bonus via stat_modifiers for testing
    sword = create_weapon("Iron Sword", base_damage=5, stat_modifiers={"strength": 2})
    helmet = create_armor("Iron Helmet", physical_defense=3, slot=EquipSlot.HEAD)
    boots = create_armor("Iron Boots", physical_defense=2, slot=EquipSlot.FEET)

    equipment.equip(sword)
    equipment.equip(helmet)
    equipment.equip(boots)

    total_strength = equipment.get_total_stat_bonus("strength")
    total_physical_defense = equipment.get_total_stat_bonus("base_physical_defense")

    assert total_strength == 2
    assert total_physical_defense == 5


def test_removing_more_items_than_exist():
    """Removing more items than exist should remove what's available."""
    inventory = Inventory(max_slots=10)

    potions = Item(
        name="Potion", item_type=ItemType.CONSUMABLE, stackable=True, quantity=3
    )

    inventory.add_item(potions)

    result = inventory.remove_item(potions, quantity=5)

    assert result is True
    assert potions not in inventory.items


def test_equipping_item_returns_previously_equipped():
    """Equipping an item should return the previously equipped item in that slot."""
    equipment = Equipment()

    sword1 = create_weapon("Iron Sword", base_damage=5)
    sword2 = create_weapon("Steel Sword", base_damage=10)

    old_item = equipment.equip(sword1)
    assert old_item is None

    old_item = equipment.equip(sword2)
    assert old_item == sword1


def test_gold_transactions():
    """Gold add/remove transactions should work correctly."""
    inventory = Inventory(max_slots=10)

    inventory.add_gold(100)
    assert inventory.gold == 100

    success = inventory.remove_gold(50)
    assert success is True
    assert inventory.gold == 50

    success = inventory.remove_gold(100)
    assert success is False
    assert inventory.gold == 50


def test_inventory_is_full():
    """is_full should correctly report when inventory is at capacity."""
    inventory = Inventory(max_slots=2)

    assert not inventory.is_full()

    inventory.add_item(Item(name="Item1", item_type=ItemType.MISC))
    assert not inventory.is_full()

    inventory.add_item(Item(name="Item2", item_type=ItemType.MISC))
    assert inventory.is_full()


def test_inventory_find_item_by_name():
    """find_item should locate items by name."""
    inventory = Inventory(max_slots=10)

    sword = create_weapon("Iron Sword", base_damage=5)
    inventory.add_item(sword)

    found = inventory.find_item("Iron Sword")

    assert found is not None
    assert found.name == "Iron Sword"


def test_inventory_has_item_with_quantity():
    """has_item should check for both name and quantity."""
    inventory = Inventory(max_slots=10)

    potions = Item(
        name="Potion", item_type=ItemType.CONSUMABLE, stackable=True, quantity=5
    )
    inventory.add_item(potions)

    assert inventory.has_item("Potion", 3) is True
    assert inventory.has_item("Potion", 5) is True
    assert inventory.has_item("Potion", 6) is False


def test_inventory_get_total_weight():
    """get_total_weight should sum up all item weights including quantities."""
    inventory = Inventory(max_slots=10)

    item1 = Item(name="Sword", item_type=ItemType.WEAPON, weight=5.0)
    item2 = Item(
        name="Arrow",
        item_type=ItemType.MATERIAL,
        weight=0.1,
        stackable=True,
        quantity=20,
    )

    inventory.add_item(item1)
    inventory.add_item(item2)

    total_weight = inventory.get_total_weight()

    assert total_weight == 5.0 + (0.1 * 20)


def test_equipment_get_all_equipped():
    """get_all_equipped should return all equipped items."""
    equipment = Equipment()

    sword = create_weapon("Sword", base_damage=5)
    helmet = create_armor("Helmet", physical_defense=3, slot=EquipSlot.HEAD)

    equipment.equip(sword)
    equipment.equip(helmet)

    all_equipped = equipment.get_all_equipped()

    assert len(all_equipped) == 2
    assert sword in all_equipped
    assert helmet in all_equipped


def test_equipment_unequip():
    """unequip should remove item from slot and return it."""
    equipment = Equipment()

    sword = create_weapon("Sword", base_damage=5)
    equipment.equip(sword)

    unequipped = equipment.unequip(EquipSlot.WEAPON)

    assert unequipped == sword
    assert equipment.is_slot_empty(EquipSlot.WEAPON)


def test_inventory_remove_item_by_name():
    """remove_item_by_name should work correctly."""
    inventory = Inventory(max_slots=10)

    sword = create_weapon("Iron Sword", base_damage=5)
    inventory.add_item(sword)

    result = inventory.remove_item_by_name("Iron Sword")

    assert result is True
    assert inventory.find_item("Iron Sword") is None


def test_inventory_find_items_by_type():
    """find_items_by_type should return all items of a specific type."""
    inventory = Inventory(max_slots=10)

    sword = create_weapon("Sword", base_damage=5)
    helmet = create_armor("Helmet", physical_defense=3, slot=EquipSlot.HEAD)
    potion = Item(name="Potion", item_type=ItemType.CONSUMABLE)

    inventory.add_item(sword)
    inventory.add_item(helmet)
    inventory.add_item(potion)

    weapons = inventory.find_items_by_type(ItemType.WEAPON)
    armor = inventory.find_items_by_type(ItemType.ARMOR)

    assert len(weapons) == 1
    assert len(armor) == 1


def test_equipment_get_all_stat_bonuses():
    """get_all_stat_bonuses should return dict of all bonuses."""
    equipment = Equipment()

    # Weapons have base_damage, not atk stat_modifiers, so give sword a stat bonus for testing
    sword = create_weapon("Sword", base_damage=10, stat_modifiers={"strength": 3})
    helmet = create_armor("Helmet", physical_defense=5, slot=EquipSlot.HEAD)

    equipment.equip(sword)
    equipment.equip(helmet)

    bonuses = equipment.get_all_stat_bonuses()

    assert bonuses["strength"] == 3
    assert bonuses["base_physical_defense"] == 5
