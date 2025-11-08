"""Tests for AI systems (legacy pathfinding implementations)."""

import pytest
from barebones_rpg.entities.ai import SimplePathfindingAI, TacticalAI
from barebones_rpg.entities.ai_interface import AIContext
from barebones_rpg.world.world import Location, Tile
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder
from barebones_rpg.entities.entity import Entity, Character, Enemy
from barebones_rpg.entities.stats import Stats


@pytest.fixture
def simple_location():
    """Create a simple location for testing."""
    loc = Location(
        name="Test Area",
        description="Test location",
        width=10,
        height=10,
    )
    # All tiles walkable
    for y in range(10):
        for x in range(10):
            loc.set_tile(x, y, Tile(x=x, y=y, tile_type="floor", walkable=True))
    return loc


@pytest.fixture
def location_with_walls():
    """Create a location with walls."""
    loc = Location(
        name="Maze",
        description="Test maze",
        width=10,
        height=10,
    )
    # Create walkable floor
    for y in range(10):
        for x in range(10):
            loc.set_tile(x, y, Tile(x=x, y=y, tile_type="floor", walkable=True))

    # Add some walls
    for y in range(2, 8):
        loc.set_tile(5, y, Tile(x=5, y=y, tile_type="wall", walkable=False))

    return loc


@pytest.fixture
def player_entity():
    """Create a player entity."""
    stats = Stats(
        strength=10,
        constitution=10,
        intelligence=10,
        dexterity=10,
        charisma=10,
        base_max_hp=100,
        hp=100,
    )
    entity = Character(name="Hero", stats=stats)
    entity.position = (0, 0)
    return entity


@pytest.fixture
def enemy_entity():
    """Create an enemy entity."""
    stats = Stats(
        strength=10,
        constitution=10,
        intelligence=10,
        dexterity=10,
        charisma=10,
        base_max_hp=50,
        hp=50,
    )
    entity = Enemy(name="Goblin", stats=stats, exp_reward=10, gold_reward=5)
    entity.position = (5, 5)
    return entity


@pytest.fixture
def weak_enemy_entity():
    """Create a weak enemy entity for flee testing."""
    stats = Stats(
        strength=5,
        constitution=5,
        intelligence=5,
        dexterity=5,
        charisma=5,
        base_max_hp=30,
        hp=5,  # Low HP to trigger flee
        max_hp=30,
    )
    entity = Enemy(name="Weak Goblin", stats=stats, exp_reward=5, gold_reward=2)
    entity.position = (5, 5)
    return entity


@pytest.fixture
def pathfinder(simple_location):
    """Create a pathfinder for testing."""
    return TilemapPathfinder(simple_location)


def test_simple_pathfinding_ai_initialization(pathfinder):
    """Test SimplePathfindingAI initialization."""
    ai = SimplePathfindingAI(pathfinder)
    assert ai.pathfinder == pathfinder
    assert ai.attack_range == 1
    assert ai.max_moves == 3


def test_simple_ai_attack_in_range(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI attacking when target is in range."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    ai = SimplePathfindingAI(pathfinder)
    context = AIContext(
        entity=enemy_entity,
        nearby_entities=[player_entity],
        metadata={"location": simple_location},
    )
    action = ai.decide_action(context)

    assert action["action"] == "attack"
    assert action["target"] == player_entity


def test_simple_ai_move_toward_target(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI moving toward target."""
    simple_location.add_entity(enemy_entity, 0, 0)
    simple_location.add_entity(player_entity, 5, 0)
    enemy_entity.position = (0, 0)
    player_entity.position = (5, 0)

    ai = SimplePathfindingAI(pathfinder)
    context = AIContext(
        entity=enemy_entity,
        nearby_entities=[player_entity],
        metadata={"location": simple_location},
    )
    action = ai.decide_action(context)

    assert action["action"] == "move"
    assert action.get("position") is not None


def test_simple_ai_wait_no_path(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI waiting when no path available."""
    ai = SimplePathfindingAI(pathfinder)
    context = AIContext(
        entity=enemy_entity,
        nearby_entities=[player_entity],
        metadata={},  # No location
    )
    action = ai.decide_action(context)

    assert action["action"] == "wait"


def test_simple_ai_custom_attack_range(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI with custom attack range."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 7)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 7)

    ai = SimplePathfindingAI(pathfinder, attack_range=2)
    context = AIContext(
        entity=enemy_entity,
        nearby_entities=[player_entity],
        metadata={"location": simple_location},
    )
    action = ai.decide_action(context)

    assert action["action"] == "attack"
    assert action["target"] == player_entity


def test_tactical_ai_initialization(pathfinder):
    """Test TacticalAI initialization."""
    ai = TacticalAI(pathfinder)
    assert ai.pathfinder == pathfinder
    assert ai.behavior_mode == "aggressive"
    assert ai.flee_hp_threshold == 0.3


def test_tactical_ai_should_flee_low_hp(weak_enemy_entity):
    """Test tactical AI flee check with low HP."""
    loc = Location(name="test", description="test", width=10, height=10)
    pathfinder = TilemapPathfinder(loc)
    ai = TacticalAI(pathfinder)

    should_flee = ai.should_flee(weak_enemy_entity)
    assert should_flee


def test_tactical_ai_should_not_flee_high_hp(enemy_entity):
    """Test tactical AI flee check with high HP."""
    loc = Location(name="test", description="test", width=10, height=10)
    pathfinder = TilemapPathfinder(loc)
    ai = TacticalAI(pathfinder)

    should_flee = ai.should_flee(enemy_entity)
    assert not should_flee


def test_tactical_ai_should_flee_no_stats():
    """Test tactical AI flee check with entity without stats."""
    minimal_stats = Stats(
        strength=1, constitution=1, intelligence=1, dexterity=1, charisma=1
    )
    entity = Enemy(name="NoStats", stats=minimal_stats, exp_reward=0, gold_reward=0)
    delattr(entity, "stats")

    loc = Location(name="test", description="test", width=10, height=10)
    pathfinder = TilemapPathfinder(loc)
    ai = TacticalAI(pathfinder)

    should_flee = ai.should_flee(entity)
    assert not should_flee


def test_tactical_ai_decide_attack(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test tactical AI attacking when healthy."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    ai = TacticalAI(pathfinder)
    context = AIContext(
        entity=enemy_entity,
        nearby_entities=[player_entity],
        metadata={"location": simple_location},
    )
    action = ai.decide_action(context)

    assert action["action"] == "attack"
    assert action["target"] == player_entity


def test_tactical_ai_decide_flee(
    pathfinder, weak_enemy_entity, player_entity, simple_location
):
    """Test tactical AI fleeing when low HP."""
    simple_location.add_entity(weak_enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    weak_enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    ai = TacticalAI(pathfinder)
    context = AIContext(
        entity=weak_enemy_entity,
        nearby_entities=[player_entity],
        metadata={"location": simple_location},
    )
    action = ai.decide_action(context)

    assert action["action"] == "flee"
    assert action["target"] == player_entity


def test_tactical_ai_set_behavior(pathfinder):
    """Test setting tactical AI behavior."""
    ai = TacticalAI(pathfinder)

    ai.set_behavior("defensive", flee_threshold=0.5)
    assert ai.behavior_mode == "defensive"
    assert ai.flee_hp_threshold == 0.5


def test_tactical_ai_set_behavior_without_threshold(pathfinder):
    """Test setting behavior without changing threshold."""
    ai = TacticalAI(pathfinder)
    original_threshold = ai.flee_hp_threshold

    ai.set_behavior("patrol")
    assert ai.behavior_mode == "patrol"
    assert ai.flee_hp_threshold == original_threshold
