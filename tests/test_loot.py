"""Tests for the loot system."""

import pytest
from barebones_rpg.items import (
    Item,
    ItemType,
    LootManager,
    LootDrop,
    roll_loot_table,
    create_loot_entry,
    create_consumable,
)
from barebones_rpg.entities import Enemy, Stats


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the loot registry before each test."""
    LootManager().clear()
    yield
    LootManager().clear()


def test_loot_registry_register_and_get():
    """Test registering and retrieving items from the registry."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Bone", bone)

    retrieved = LootManager().get("Bone")
    assert retrieved is not None
    assert retrieved.name == "Bone"
    assert retrieved.value == 5
    assert retrieved.id != bone.id  # Should be a different instance


def test_loot_registry_get_nonexistent():
    """Test getting a non-existent item returns None."""
    result = LootManager().get("DoesNotExist")
    assert result is None


def test_loot_registry_has():
    """Test checking if an item is registered."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Bone", bone)

    assert LootManager().has("Bone")
    assert not LootManager().has("DoesNotExist")


def test_loot_registry_clear():
    """Test clearing the registry."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Bone", bone)

    assert LootManager().has("Bone")

    LootManager().clear()

    assert not LootManager().has("Bone")


def test_loot_registry_with_factory_function():
    """Test registering a factory function."""

    def create_bone():
        return Item(name="Bone", item_type=ItemType.MATERIAL, value=5)

    LootManager().register("Bone", create_bone)

    item1 = LootManager().get("Bone")
    item2 = LootManager().get("Bone")

    assert item1 is not None
    assert item2 is not None
    assert item1.id != item2.id  # Different instances


def test_loot_registry_factory_returns_none():
    """Test factory function that returns None."""

    def create_nothing():
        return None

    LootManager().register("Nothing", create_nothing)

    result = LootManager().get("Nothing")
    assert result is None


def test_loot_registry_unique_item():
    """Test that unique items only drop once."""
    unique_sword = Item(
        name="Legendary Sword", item_type=ItemType.WEAPON, unique=True, base_damage=50
    )
    LootManager().register("Legendary Sword", unique_sword)

    first_drop = LootManager().get("Legendary Sword")
    assert first_drop is not None

    second_drop = LootManager().get("Legendary Sword")
    assert second_drop is None  # Already dropped


def test_loot_registry_reset_unique_tracking():
    """Test resetting unique item tracking."""
    unique_sword = Item(
        name="Legendary Sword", item_type=ItemType.WEAPON, unique=True, base_damage=50
    )
    LootManager().register("Legendary Sword", unique_sword)

    first_drop = LootManager().get("Legendary Sword")
    assert first_drop is not None

    LootManager().reset_unique_tracking()

    second_drop = LootManager().get("Legendary Sword")
    assert second_drop is not None  # Can drop again after reset


def test_roll_loot_table_with_string_items():
    """Test rolling on a loot table with string item references."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Bone", bone)

    loot_table = [{"item": "Bone", "chance": 1.0}]  # 100% drop

    drops = roll_loot_table(loot_table)

    assert len(drops) == 1
    assert drops[0].item.name == "Bone"
    assert drops[0].quantity == 1


def test_roll_loot_table_with_item_objects():
    """Test rolling on a loot table with direct Item objects."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)

    loot_table = [{"item": bone, "chance": 1.0}]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 1
    assert drops[0].item.name == "Bone"
    assert drops[0].item.id != bone.id  # Should be a copy


def test_roll_loot_table_with_mixed_entries():
    """Test rolling on a loot table with both strings and Item objects."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    scale = Item(name="Scale", item_type=ItemType.MATERIAL, value=10)

    LootManager().register("Bone", bone)

    loot_table = [
        {"item": "Bone", "chance": 1.0},
        {"item": scale, "chance": 1.0},
    ]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 2
    assert any(drop.item.name == "Bone" for drop in drops)
    assert any(drop.item.name == "Scale" for drop in drops)


def test_roll_loot_table_probability():
    """Test that probability works correctly (statistical test)."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Bone", bone)

    loot_table = [{"item": "Bone", "chance": 0.5}]  # 50% drop

    # Roll 1000 times
    drop_count = 0
    for _ in range(1000):
        drops = roll_loot_table(loot_table)
        if drops:
            drop_count += 1

    # Should be roughly 500 (within reasonable margin)
    assert 400 < drop_count < 600


def test_roll_loot_table_missing_item_in_registry():
    """Test that missing items in registry are skipped gracefully."""
    loot_table = [{"item": "DoesNotExist", "chance": 1.0}]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 0  # No error, just no drops


def test_roll_loot_table_invalid_format():
    """Test that invalid loot table entries are skipped."""
    loot_table = [
        "not a dict",
        {"no_item_key": "value"},
        {"item": "Test", "no_chance_key": 0.5},
        {"item": "Test", "chance": 1.5},  # Invalid chance > 1.0
        {"item": "Test", "chance": -0.5},  # Invalid chance < 0.0
    ]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 0


def test_roll_loot_table_with_quantity():
    """Test rolling with explicit quantity."""
    bone = Item(
        name="Bone", item_type=ItemType.MATERIAL, value=5, stackable=True, max_stack=99
    )

    loot_table = [{"item": bone, "chance": 1.0, "quantity": 5}]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 1
    assert drops[0].item.quantity == 5
    assert drops[0].quantity == 5


def test_roll_loot_table_with_min_max_quantity():
    """Test rolling with min and max quantity."""
    bone = Item(
        name="Bone", item_type=ItemType.MATERIAL, value=5, stackable=True, max_stack=99
    )

    loot_table = [{"item": bone, "chance": 1.0, "min_quantity": 3, "max_quantity": 7}]

    drops = roll_loot_table(loot_table)

    assert len(drops) == 1
    assert 3 <= drops[0].item.quantity <= 7
    assert 3 <= drops[0].quantity <= 7


def test_roll_loot_table_with_source():
    """Test that source is properly attached to drops."""
    enemy = Enemy(name="Goblin", stats=Stats())
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)

    loot_table = [{"item": bone, "chance": 1.0}]

    drops = roll_loot_table(loot_table, source=enemy)

    assert len(drops) == 1
    assert drops[0].source == enemy


def test_create_loot_entry():
    """Test the create_loot_entry helper function."""
    entry = create_loot_entry("Bone", 0.5, quantity=3)

    assert entry["item"] == "Bone"
    assert entry["chance"] == 0.5
    assert entry["quantity"] == 3


def test_enemy_with_loot_table():
    """Test creating an enemy with a loot table."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)

    enemy = Enemy(
        name="Goblin",
        stats=Stats(),
        loot_table=[{"item": bone, "chance": 0.3}, {"item": "Scale", "chance": 0.1}],
    )

    assert len(enemy.loot_table) == 2
    assert enemy.loot_table[0]["chance"] == 0.3
    assert enemy.loot_table[1]["item"] == "Scale"


def test_loot_drop_dataclass():
    """Test the LootDrop dataclass."""
    bone = Item(name="Bone", item_type=ItemType.MATERIAL, value=5)
    enemy = Enemy(name="Goblin", stats=Stats())

    drop = LootDrop(item=bone, source=enemy, quantity=3)

    assert drop.item == bone
    assert drop.source == enemy
    assert drop.quantity == 3


def test_unique_item_field():
    """Test that unique field is properly set on items."""
    regular_item = Item(name="Bone", item_type=ItemType.MATERIAL)
    assert regular_item.unique is False

    unique_item = Item(name="Legendary Sword", item_type=ItemType.WEAPON, unique=True)
    assert unique_item.unique is True


def test_loot_table_respects_max_stack():
    """Test that loot respects max_stack for stackable items."""
    bone = Item(
        name="Bone",
        item_type=ItemType.MATERIAL,
        value=5,
        stackable=True,
        max_stack=10,
    )

    loot_table = [{"item": bone, "chance": 1.0, "quantity": 50}]  # More than max

    drops = roll_loot_table(loot_table)

    assert len(drops) == 1
    assert drops[0].item.quantity == 10  # Should be capped at max_stack


def test_unique_item_only_drops_once_with_registry():
    """Test that unique items registered in LootManager only drop once."""
    # Create and register a unique item
    legendary_sword = Item(
        name="Legendary Sword",
        item_type=ItemType.WEAPON,
        unique=True,
        base_damage=50,
        value=10000,
    )
    LootManager().register("Legendary Sword", legendary_sword)

    # Create loot table with 100% drop chance
    loot_table = [{"item": "Legendary Sword", "chance": 1.0}]

    # Roll on the table multiple times (simulating multiple enemies)
    drops1 = roll_loot_table(loot_table)
    drops2 = roll_loot_table(loot_table)
    drops3 = roll_loot_table(loot_table)

    # Should only drop once
    assert len(drops1) == 1
    assert len(drops2) == 0
    assert len(drops3) == 0
    assert drops1[0].item.name == "Legendary Sword"


def test_unique_item_only_drops_once_direct_object():
    """Test that unique items used directly only drop once."""
    # Create a unique item (not in registry)
    legendary_axe = Item(
        name="Legendary Axe",
        item_type=ItemType.WEAPON,
        unique=True,
        base_damage=60,
        value=15000,
    )

    # Use the same item object in loot table for multiple enemies
    loot_table = [{"item": legendary_axe, "chance": 1.0}]

    # Roll on the table multiple times
    drops1 = roll_loot_table(loot_table)
    drops2 = roll_loot_table(loot_table)
    drops3 = roll_loot_table(loot_table)

    # With direct objects, each gets a copy so it should drop each time
    # (unique tracking only works with registry)
    assert len(drops1) == 1
    assert len(drops2) == 1
    assert len(drops3) == 1
    # But each should have a different ID
    assert drops1[0].item.id != drops2[0].item.id
    assert drops2[0].item.id != drops3[0].item.id


def test_multiple_enemies_with_same_unique_drop():
    """Test realistic scenario: multiple enemies, same unique item, only drops once."""
    # Register a unique item
    unique_ring = Item(
        name="Ring of Power",
        item_type=ItemType.ACCESSORY,
        unique=True,
        stat_modifiers={"atk": 10, "defense": 10},
        value=5000,
    )
    LootManager().register("Ring of Power", unique_ring)

    # Create 3 bosses that all have 100% chance to drop the ring
    boss1_loot = [{"item": "Ring of Power", "chance": 1.0}]
    boss2_loot = [{"item": "Ring of Power", "chance": 1.0}]
    boss3_loot = [{"item": "Ring of Power", "chance": 1.0}]

    # Simulate killing all 3 bosses
    drops_from_boss1 = roll_loot_table(boss1_loot)
    drops_from_boss2 = roll_loot_table(boss2_loot)
    drops_from_boss3 = roll_loot_table(boss3_loot)

    # Count total rings dropped
    total_rings = len(drops_from_boss1) + len(drops_from_boss2) + len(drops_from_boss3)

    # Only one ring should have dropped across all 3 bosses
    assert total_rings == 1
    # And it should be from the first boss
    assert len(drops_from_boss1) == 1
    assert drops_from_boss1[0].item.name == "Ring of Power"
