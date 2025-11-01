"""Shared fixtures for tests."""

import pytest
from barebones_rpg.core.events import EventManager, Event, EventType
from barebones_rpg.entities.stats import Stats, StatusEffect, StatsManager
from barebones_rpg.entities.entity import Entity, Character, Enemy
from barebones_rpg.items.item import (
    Item,
    ItemType,
    EquipSlot,
    create_weapon,
    create_consumable,
)
from barebones_rpg.items.inventory import Inventory, Equipment


@pytest.fixture
def event_manager():
    """Create a fresh EventManager instance."""
    return EventManager()


@pytest.fixture
def basic_stats():
    """Create basic stats for testing."""
    return Stats(
        strength=15,
        constitution=10,
        intelligence=10,  # 10 INT → max_mp = 20 + (10*3) = 50
        dexterity=12,
        charisma=10,
        base_max_hp=50,
        base_max_mp=20,
        hp=100,
        mp=50,
    )


@pytest.fixture
def basic_entity(basic_stats):
    """Create a basic entity for testing."""
    return Entity(name="Test Entity", stats=basic_stats)


@pytest.fixture
def basic_character():
    """Create a basic character for testing."""
    stats = Stats(
        strength=15,
        constitution=12,
        intelligence=10,
        dexterity=14,
        charisma=10,
        base_max_hp=50,
        base_max_mp=20,
        hp=100,
        mp=50,
        level=1,
        exp=0,
        exp_to_next=100,
    )
    return Character(name="Hero", stats=stats)


@pytest.fixture
def basic_enemy():
    """Create a basic enemy for testing."""
    stats = Stats(
        strength=10,
        constitution=8,
        intelligence=5,
        dexterity=10,
        charisma=5,
        base_max_hp=30,
        base_max_mp=0,
        hp=50,
        mp=0,
    )
    return Enemy(name="Goblin", stats=stats, exp_reward=25, gold_reward=10)


@pytest.fixture
def inventory():
    """Create an empty inventory for testing."""
    return Inventory(max_slots=10, max_weight=-1)


@pytest.fixture
def equipment():
    """Create empty equipment for testing."""
    return Equipment()


@pytest.fixture
def sample_weapon():
    """Create a sample weapon item."""
    return create_weapon("Iron Sword", base_damage=5, damage_type="physical", value=100)


@pytest.fixture
def sample_consumable():
    """Create a sample consumable item."""

    def heal_effect(target, context):
        return target.heal(30)

    return create_consumable(
        "Health Potion", on_use=heal_effect, value=50, stackable=True, max_stack=99
    )
