"""Tests for the item system."""

import pytest
from barebones_rpg.items.item import Item, ItemType, create_consumable
from barebones_rpg.entities.entity import Entity
from barebones_rpg.entities.stats import Stats


def test_stackable_items_with_overflow():
    """Stackable items should handle overflow when exceeding max_stack."""
    item1 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=8,
    )
    item2 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=5,
    )

    overflow = item1.stack_with(item2)

    assert item1.quantity == 10
    assert overflow == 3


def test_stackable_items_no_overflow():
    """Stackable items with no overflow should stack completely."""
    item1 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=5,
    )
    item2 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=3,
    )

    overflow = item1.stack_with(item2)

    assert item1.quantity == 8
    assert overflow == 0


def test_splitting_stacks_creates_new_item():
    """Splitting a stack should create a new item with correct quantity."""
    item = Item(name="Arrow", item_type=ItemType.MATERIAL, stackable=True, quantity=20)

    new_item = item.split(7)

    assert item.quantity == 13
    assert new_item.quantity == 7
    assert new_item.name == item.name
    assert new_item.id != item.id


def test_items_with_same_name_different_ids_can_stack():
    """Items with same name but different IDs should be able to stack."""
    item1 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=5,
    )
    item2 = Item(
        name="Potion",
        item_type=ItemType.CONSUMABLE,
        stackable=True,
        max_stack=10,
        quantity=3,
    )

    assert item1.id != item2.id
    assert item1.can_stack_with(item2)


def test_non_stackable_items_dont_stack():
    """Non-stackable items should not stack."""
    sword1 = Item(name="Iron Sword", item_type=ItemType.WEAPON, stackable=False)
    sword2 = Item(name="Iron Sword", item_type=ItemType.WEAPON, stackable=False)

    assert not sword1.can_stack_with(sword2)


def test_consumable_items_reduce_quantity_on_use():
    """Consumable items should reduce quantity when used."""
    entity = Entity(name="Hero", stats=Stats(constitution=10, base_max_hp=50, hp=50))

    def heal_effect(target, context):
        return target.heal(30)

    potion = create_consumable(
        "Health Potion", on_use=heal_effect, stackable=True, max_stack=99
    )
    potion.quantity = 5

    potion.use(entity)

    assert potion.quantity == 4
    assert entity.stats.hp == 80


def test_splitting_at_boundary_amount_equals_zero():
    """Splitting with amount=0 should return None."""
    item = Item(name="Arrow", item_type=ItemType.MATERIAL, stackable=True, quantity=10)

    result = item.split(0)

    assert result is None
    assert item.quantity == 10


def test_splitting_at_boundary_amount_equals_quantity():
    """Splitting with amount >= quantity should return None."""
    item = Item(name="Arrow", item_type=ItemType.MATERIAL, stackable=True, quantity=10)

    result = item.split(10)

    assert result is None
    assert item.quantity == 10


def test_splitting_non_stackable_returns_none():
    """Splitting a non-stackable item should return None."""
    sword = Item(name="Iron Sword", item_type=ItemType.WEAPON, stackable=False)

    result = sword.split(1)

    assert result is None


def test_item_can_stack_with_requires_same_name():
    """Items can only stack if they have the same name."""
    potion = Item(name="Health Potion", item_type=ItemType.CONSUMABLE, stackable=True)
    ether = Item(name="Mana Potion", item_type=ItemType.CONSUMABLE, stackable=True)

    assert not potion.can_stack_with(ether)


def test_item_can_stack_with_requires_different_instances():
    """Items cannot stack with themselves (same ID)."""
    potion = Item(name="Health Potion", item_type=ItemType.CONSUMABLE, stackable=True)

    assert not potion.can_stack_with(potion)


def test_item_use_without_on_use_callback():
    """Using an item without on_use callback should return None."""
    item = Item(name="Quest Item", item_type=ItemType.QUEST, on_use=None)
    entity = Entity(name="Hero", stats=Stats())

    result = item.use(entity)

    assert result is None


def test_item_to_dict_excludes_on_use():
    """Item serialization should handle on_use callback."""

    def heal(target, context):
        return target.heal(50)

    potion = create_consumable("Health Potion", on_use=heal)

    data = potion.to_dict()

    assert "on_use" not in data
    assert data["name"] == "Health Potion"
