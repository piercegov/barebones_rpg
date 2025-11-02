"""Tests for the entity system."""

import pytest
from barebones_rpg.entities.entity import Entity, Character, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.core.events import EventManager, EventType


def test_entity_defense_reduces_damage_but_minimum_1():
    """Entity defense should reduce damage with minimum 0 (new damage formula)."""
    stats = Stats(constitution=20, base_physical_defense=10, hp=100)
    entity = Entity(name="Tank", stats=stats)

    attacker_stats = Stats(strength=15)
    attacker = Entity(name="Weak Attacker", stats=attacker_stats)

    damage_taken = entity.take_damage(15, attacker)

    # Damage: 15 - (10 base + 10 from CON) = 15 - 20 = 0 (clamped to 0)
    assert damage_taken == 0
    assert entity.stats.hp == 100  # No damage taken


def test_entity_defense_reduces_damage_normally():
    """Normal damage reduction by defense."""
    stats = Stats(
        constitution=4, base_physical_defense=3, hp=100
    )  # defense = 3 + (4*0.5) = 5
    entity = Entity(name="Defender", stats=stats)

    damage_taken = entity.take_damage(20)

    assert damage_taken == 15  # 20 - 5 = 15
    assert entity.stats.hp == 85


def test_healing_caps_at_max_hp():
    """Healing should cap at max_hp."""
    entity = Entity(name="Wounded", stats=Stats(constitution=10, base_max_hp=50, hp=50))

    healed = entity.heal(100)

    assert entity.stats.hp == 100
    assert healed == 50


def test_character_leveling_single_level():
    """Character should level up when gaining enough exp."""
    character = Character(
        name="Hero",
        stats=Stats(
            constitution=10, level=1, exp=0, exp_to_next=100, base_max_hp=50, hp=100
        ),
    )

    leveled_up = character.gain_exp(100)

    assert leveled_up is True
    assert character.stats.level == 2
    assert character.stats.exp == 0


def test_character_leveling_exp_overflow():
    """Exp overflow should carry to next level."""
    character = Character(
        name="Hero",
        stats=Stats(
            constitution=10, level=1, exp=80, exp_to_next=100, base_max_hp=50, hp=100
        ),
    )

    leveled_up = character.gain_exp(30)

    assert leveled_up is True
    assert character.stats.level == 2
    assert character.stats.exp == 10


def test_character_multiple_level_ups_in_one_call():
    """Multiple level-ups should happen in one gain_exp call."""
    character = Character(
        name="Hero",
        stats=Stats(
            constitution=10, level=1, exp=0, exp_to_next=100, base_max_hp=50, hp=100
        ),
    )

    leveled_up = character.gain_exp(300)

    assert leveled_up is True
    assert character.stats.level > 2


def test_character_level_up_stats_increase():
    """Leveling up should give stat points."""
    character = Character(
        name="Hero",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=10,
            dexterity=10,
            charisma=10,
            level=1,
            exp=0,
            exp_to_next=100,
            base_max_hp=50,
            base_max_mp=20,
            hp=100,
            mp=50,
            stat_points=0,
        ),
    )

    old_stat_points = character.stats.stat_points

    character.gain_exp(100)

    # Leveling up should grant stat points
    assert character.stats.stat_points > old_stat_points
    assert character.stats.hp == character.stats.get_max_hp()  # HP restored to max


def test_entity_action_callbacks_registration():
    """Entities should be able to register custom action callbacks."""
    entity = Entity(name="Test")

    call_count = {"count": 0}

    def custom_action(ent, **kwargs):
        call_count["count"] += 1
        return kwargs.get("value", 0)

    entity.register_action("custom_action", custom_action)

    results = entity.perform_action("custom_action", value=42)

    assert call_count["count"] == 1
    assert results[0] == 42


def test_entity_action_callbacks_multiple():
    """Multiple callbacks can be registered for the same action."""
    entity = Entity(name="Test")

    results_list = []

    def action1(ent, **kwargs):
        results_list.append("action1")

    def action2(ent, **kwargs):
        results_list.append("action2")

    entity.register_action("test", action1)
    entity.register_action("test", action2)

    entity.perform_action("test")

    assert len(results_list) == 2
    assert "action1" in results_list
    assert "action2" in results_list


def test_inventory_equipment_lazy_loading():
    """Inventory and equipment should be lazily initialized."""
    entity = Entity(name="Test")

    assert entity.inventory is None
    assert entity.equipment is None

    inventory = entity.init_inventory()
    equipment = entity.init_equipment()

    assert inventory is not None
    assert equipment is not None
    assert entity.inventory is inventory
    assert entity.equipment is equipment


def test_can_perform_action_when_dead():
    """Dead entities should not be able to perform actions."""
    entity = Entity(name="Test", stats=Stats(hp=0))

    assert not entity.can_perform_action()


def test_can_perform_action_when_alive():
    """Living entities should be able to perform actions."""
    entity = Entity(name="Test", stats=Stats(hp=100))

    assert entity.can_perform_action()


def test_character_gain_exp_publishes_event():
    """Gaining exp and leveling up should publish LEVEL_UP event."""
    events = EventManager()
    events.enable_history()

    character = Character(
        name="Hero",
        stats=Stats(
            constitution=10, level=1, exp=0, exp_to_next=100, base_max_hp=50, hp=100
        ),
    )

    character.gain_exp(100, events)

    history = events.get_history()
    level_up_events = [e for e in history if e.event_type == EventType.LEVEL_UP]

    assert len(level_up_events) == 1
    assert level_up_events[0].data["entity"] == character


def test_entity_to_dict_and_from_dict():
    """Entities should be serializable to/from dict."""
    entity = Entity(name="Test", stats=Stats(strength=15, hp=100))

    data = entity.to_dict()

    assert data["name"] == "Test"
    assert data["stats"]["hp"] == 100

    restored = Entity.from_dict(data)
    assert restored.name == "Test"
    assert restored.stats.hp == 100
