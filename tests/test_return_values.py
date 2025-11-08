"""Tests for return values of add/remove/set operations."""

import pytest

from barebones_rpg.entities import Entity, Stats, StatsManager
from barebones_rpg.quests import Quest, QuestObjective, QuestManager, ObjectiveType
from barebones_rpg.combat.combat import CombatantGroup
from barebones_rpg.dialog import DialogTree, DialogNode
from barebones_rpg.world import World, Location, Tile
from barebones_rpg.entities.stats import StatusEffect


def test_combat_group_add_member_returns_true():
    """Adding a member to combat group should return True."""
    group = CombatantGroup(name="Heroes")
    member = Entity(name="Hero", stats=Stats())

    result = group.add_member(member)

    assert result is True
    assert member in group.members


def test_combat_group_remove_member_returns_true_when_found():
    """Removing an existing member should return True."""
    group = CombatantGroup(name="Heroes")
    member = Entity(name="Hero", stats=Stats())
    group.add_member(member)

    result = group.remove_member(member)

    assert result is True
    assert member not in group.members


def test_combat_group_remove_member_returns_false_when_not_found():
    """Removing a non-existent member should return False."""
    group = CombatantGroup(name="Heroes")
    member = Entity(name="Hero", stats=Stats())

    result = group.remove_member(member)

    assert result is False


def test_quest_add_objective_returns_true():
    """Adding an objective to quest should return True."""
    quest = Quest(name="Test Quest", description="Test")
    objective = QuestObjective(
        description="Test Objective", objective_type=ObjectiveType.CUSTOM
    )

    result = quest.add_objective(objective)

    assert result is True
    assert objective in quest.objectives


def test_quest_manager_add_quest_returns_true():
    """Adding a quest to manager should return True."""
    from barebones_rpg.quests.quest import QuestManager

    # Get the singleton manager
    manager = QuestManager()

    # Create a quest with a specific ID to test
    quest = Quest(
        id="test_quest_return_value_123", name="Test Quest", description="Test"
    )

    # Explicitly add the quest to the manager
    result = manager.add_quest(quest)

    # Check that add_quest returned True
    assert result is True

    # Verify the quest is registered
    retrieved = manager.get_quest("test_quest_return_value_123")
    assert retrieved is not None
    assert retrieved.name == "Test Quest"


def test_dialog_tree_add_node_returns_true():
    """Adding a node to dialog tree should return True."""
    tree = DialogTree(name="Test Tree")
    node = DialogNode(id="start", text="Hello")

    result = tree.add_node(node)

    assert result is True
    assert tree.get_node("start") is not None


def test_dialog_tree_set_start_node_returns_true_when_exists():
    """Setting start node to existing node should return True."""
    tree = DialogTree(name="Test Tree")
    node = DialogNode(id="start", text="Hello")
    tree.add_node(node)

    result = tree.set_start_node("start")

    assert result is True
    assert tree.start_node_id == "start"


def test_dialog_tree_set_start_node_returns_false_when_not_exists():
    """Setting start node to non-existent node should return False."""
    tree = DialogTree(name="Test Tree")

    result = tree.set_start_node("nonexistent")

    assert result is False
    assert tree.start_node_id is None


def test_world_add_location_returns_true():
    """Adding a location to world should return True."""
    world = World(name="Test World")
    location = Location(name="Village", width=10, height=10)

    result = world.add_location(location)

    assert result is True
    assert world.get_location(location.id) is not None


def test_location_add_entity_returns_true_on_success():
    """Adding an entity to location should return True."""
    location = Location(name="Test", width=10, height=10)
    entity = Entity(name="Hero", stats=Stats())

    result = location.add_entity(entity, 5, 5)

    assert result is True
    assert entity in location.entities


def test_location_add_entity_returns_false_when_already_present():
    """Adding an already present entity should return False."""
    location = Location(name="Test", width=10, height=10)
    entity = Entity(name="Hero", stats=Stats())
    location.add_entity(entity, 5, 5)

    result = location.add_entity(entity, 6, 6)

    assert result is False


def test_stats_set_stat_returns_true():
    """Setting a stat should return True."""
    stats = Stats(hp=100)

    result = stats.set_stat("hp", 150)

    assert result is True
    assert stats.hp == 150


def test_stats_add_status_effect_returns_true():
    """Adding a status effect should return True."""
    manager = StatsManager(Stats())
    effect = StatusEffect(name="Poison", duration=3)

    result = manager.add_status_effect(effect)

    assert result is True
    assert effect in manager.status_effects


def test_stats_remove_status_effect_returns_true_when_found():
    """Removing an existing status effect should return True."""
    manager = StatsManager(Stats())
    effect = StatusEffect(name="Poison", duration=3)
    manager.add_status_effect(effect)

    result = manager.remove_status_effect("Poison")

    assert result is True
    assert effect not in manager.status_effects


def test_stats_remove_status_effect_returns_false_when_not_found():
    """Removing a non-existent status effect should return False."""
    manager = StatsManager(Stats())

    result = manager.remove_status_effect("Nonexistent")

    assert result is False
