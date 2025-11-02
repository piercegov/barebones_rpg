"""Tests for AI systems."""

import pytest
from barebones_rpg.entities.ai import SimplePathfindingAI, TacticalAI, AIController
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


def test_simple_ai_attack_in_range(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI attacking when target is in range."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    ai = SimplePathfindingAI(pathfinder)
    attacked = ai.process_turn(
        enemy_entity, player_entity, simple_location, max_moves=3, on_attack=on_attack
    )

    assert attacked
    assert len(attack_called) == 1
    assert attack_called[0][0] == enemy_entity
    assert attack_called[0][1] == player_entity


def test_simple_ai_move_toward_target(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI moving toward target."""
    simple_location.add_entity(enemy_entity, 0, 0)
    simple_location.add_entity(player_entity, 5, 0)
    enemy_entity.position = (0, 0)
    player_entity.position = (5, 0)

    ai = SimplePathfindingAI(pathfinder)
    attacked = ai.process_turn(
        enemy_entity, player_entity, simple_location, max_moves=3
    )

    assert not attacked  # Too far to attack
    assert enemy_entity.position != (0, 0)  # Should have moved
    # Should be closer to target
    old_distance = 5
    new_distance = abs(enemy_entity.position[0] - 5)
    assert new_distance < old_distance


def test_simple_ai_move_and_attack(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI moving and attacking in same turn."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 7)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 7)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    ai = SimplePathfindingAI(pathfinder)
    attacked = ai.process_turn(
        enemy_entity, player_entity, simple_location, max_moves=3, on_attack=on_attack
    )

    # Should move one tile and then attack
    assert attacked
    assert len(attack_called) == 1


def test_simple_ai_blocked_path(location_with_walls, enemy_entity, player_entity):
    """Test AI behavior when path is blocked."""
    location_with_walls.add_entity(enemy_entity, 0, 5)
    location_with_walls.add_entity(player_entity, 9, 5)
    enemy_entity.position = (0, 5)
    player_entity.position = (9, 5)

    pathfinder = TilemapPathfinder(location_with_walls)
    ai = SimplePathfindingAI(pathfinder)

    attacked = ai.process_turn(
        enemy_entity, player_entity, location_with_walls, max_moves=5
    )

    assert not attacked
    # Should try to move around walls
    assert enemy_entity.position != (0, 5)


def test_simple_ai_occupied_tile(pathfinder, simple_location):
    """Test AI behavior when next tile is occupied."""
    enemy = Enemy(
        name="Enemy1",
        stats=Stats(
            strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
        ),
        exp_reward=10,
        gold_reward=5,
    )
    blocker = Enemy(
        name="Enemy2",
        stats=Stats(
            strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
        ),
        exp_reward=10,
        gold_reward=5,
    )
    player = Character(
        name="Hero",
        stats=Stats(
            strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
        ),
    )

    simple_location.add_entity(enemy, 0, 0)
    simple_location.add_entity(blocker, 1, 0)
    simple_location.add_entity(player, 5, 0)

    enemy.position = (0, 0)
    blocker.position = (1, 0)
    player.position = (5, 0)

    ai = SimplePathfindingAI(pathfinder)
    attacked = ai.process_turn(enemy, player, simple_location, max_moves=3)

    assert not attacked
    # Enemy position should not change if blocked
    # (depends on implementation, might try alternate path)


def test_simple_ai_custom_attack_range(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test AI with custom attack range."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 7)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 7)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    ai = SimplePathfindingAI(pathfinder)
    # With attack range 2, should attack without moving
    attacked = ai.process_turn(
        enemy_entity,
        player_entity,
        simple_location,
        max_moves=3,
        on_attack=on_attack,
        attack_range=2,
    )

    assert attacked
    assert enemy_entity.position == (5, 5)  # Didn't need to move


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
    # Create a minimal stats object for validation
    minimal_stats = Stats(
        strength=1, constitution=1, intelligence=1, dexterity=1, charisma=1
    )
    entity = Enemy(name="NoStats", stats=minimal_stats, exp_reward=0, gold_reward=0)
    # Remove stats attribute to test handling of entities without stats
    delattr(entity, "stats")

    loc = Location(name="test", description="test", width=10, height=10)
    pathfinder = TilemapPathfinder(loc)
    ai = TacticalAI(pathfinder)

    should_flee = ai.should_flee(entity)
    assert not should_flee


def test_tactical_ai_flee_from(
    pathfinder, weak_enemy_entity, player_entity, simple_location
):
    """Test tactical AI fleeing from target."""
    simple_location.add_entity(weak_enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 4)
    weak_enemy_entity.position = (5, 5)
    player_entity.position = (5, 4)

    ai = TacticalAI(pathfinder)
    ai.flee_from(weak_enemy_entity, player_entity, simple_location, max_moves=2)

    # Should have moved away from player
    old_distance = 1
    new_distance = abs(weak_enemy_entity.position[1] - player_entity.position[1])
    assert new_distance > old_distance or weak_enemy_entity.position[0] != 5


def test_tactical_ai_flee_blocked(location_with_walls):
    """Test tactical AI fleeing when path is blocked."""
    stats = Stats(
        strength=5,
        constitution=5,
        intelligence=5,
        dexterity=5,
        charisma=5,
        base_max_hp=30,
        hp=5,
        max_hp=30,
    )
    enemy = Enemy(name="Cornered", stats=stats, exp_reward=5, gold_reward=2)
    player = Character(
        name="Hero",
        stats=Stats(
            strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
        ),
    )

    location_with_walls.add_entity(enemy, 5, 0)
    location_with_walls.add_entity(player, 5, 1)
    enemy.position = (5, 0)
    player.position = (5, 1)

    pathfinder = TilemapPathfinder(location_with_walls)
    ai = TacticalAI(pathfinder)
    ai.flee_from(enemy, player, location_with_walls, max_moves=2)

    # May or may not move depending on available tiles


def test_tactical_ai_process_turn_attack(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test tactical AI attacking when healthy."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    ai = TacticalAI(pathfinder)
    attacked = ai.process_turn(
        enemy_entity, player_entity, simple_location, max_moves=3, on_attack=on_attack
    )

    assert attacked
    assert len(attack_called) == 1


def test_tactical_ai_process_turn_flee(
    pathfinder, weak_enemy_entity, player_entity, simple_location
):
    """Test tactical AI fleeing when low HP."""
    simple_location.add_entity(weak_enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    weak_enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    ai = TacticalAI(pathfinder)
    attacked = ai.process_turn(
        weak_enemy_entity, player_entity, simple_location, max_moves=3
    )

    assert not attacked
    # Should have moved away
    distance = abs(weak_enemy_entity.position[1] - player_entity.position[1])
    assert distance > 1 or weak_enemy_entity.position[0] != 5


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


def test_ai_controller_initialization(pathfinder):
    """Test AIController initialization."""
    controller = AIController(pathfinder, default_ai_type="simple")

    assert controller.pathfinder == pathfinder
    assert controller.default_ai_type == "simple"
    assert len(controller.ai_instances) == 0


def test_ai_controller_get_ai_for_entity_simple(pathfinder, enemy_entity):
    """Test getting simple AI for entity."""
    controller = AIController(pathfinder, default_ai_type="simple")

    ai = controller.get_ai_for_entity(enemy_entity)

    assert isinstance(ai, SimplePathfindingAI)
    assert enemy_entity.id in controller.ai_instances


def test_ai_controller_get_ai_for_entity_tactical(pathfinder, enemy_entity):
    """Test getting tactical AI for entity."""
    controller = AIController(pathfinder, default_ai_type="tactical")

    ai = controller.get_ai_for_entity(enemy_entity)

    assert isinstance(ai, TacticalAI)


def test_ai_controller_get_ai_cached(pathfinder, enemy_entity):
    """Test that AI instances are cached."""
    controller = AIController(pathfinder)

    ai1 = controller.get_ai_for_entity(enemy_entity)
    ai2 = controller.get_ai_for_entity(enemy_entity)

    assert ai1 is ai2


def test_ai_controller_process_entity_turn(
    pathfinder, enemy_entity, player_entity, simple_location
):
    """Test processing entity turn through controller."""
    simple_location.add_entity(enemy_entity, 5, 5)
    simple_location.add_entity(player_entity, 5, 6)
    enemy_entity.position = (5, 5)
    player_entity.position = (5, 6)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    controller = AIController(pathfinder)
    attacked = controller.process_entity_turn(
        enemy_entity, player_entity, simple_location, max_moves=3, on_attack=on_attack
    )

    assert attacked
    assert len(attack_called) == 1


def test_ai_controller_process_all_enemies(pathfinder, player_entity, simple_location):
    """Test processing all enemy turns."""
    enemy1 = Enemy(
        name="Goblin1",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=10,
            dexterity=10,
            charisma=10,
            base_max_hp=50,
            hp=50,
        ),
        exp_reward=10,
        gold_reward=5,
    )
    enemy2 = Enemy(
        name="Goblin2",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=10,
            dexterity=10,
            charisma=10,
            base_max_hp=50,
            hp=50,
        ),
        exp_reward=10,
        gold_reward=5,
    )

    simple_location.add_entity(enemy1, 5, 5)
    simple_location.add_entity(enemy2, 6, 6)
    simple_location.add_entity(player_entity, 5, 6)

    enemy1.position = (5, 5)
    enemy2.position = (6, 6)
    player_entity.position = (5, 6)

    attack_called = []

    def on_attack(attacker, target):
        attack_called.append((attacker, target))

    controller = AIController(pathfinder)
    controller.process_all_enemies(
        [enemy1, enemy2],
        player_entity,
        simple_location,
        max_moves_per_enemy=3,
        on_attack=on_attack,
    )

    # At least one enemy should attack
    assert len(attack_called) >= 1


def test_ai_controller_set_entity_ai_type(pathfinder, enemy_entity):
    """Test setting specific AI type for entity."""
    controller = AIController(pathfinder, default_ai_type="simple")

    # First get default
    ai1 = controller.get_ai_for_entity(enemy_entity)
    assert isinstance(ai1, SimplePathfindingAI)

    # Change to tactical
    controller.set_entity_ai_type(enemy_entity, "tactical")
    ai2 = controller.get_ai_for_entity(enemy_entity)
    assert isinstance(ai2, TacticalAI)


def test_ai_controller_set_entity_ai_type_simple(pathfinder, enemy_entity):
    """Test setting entity AI type back to simple."""
    controller = AIController(pathfinder, default_ai_type="tactical")

    controller.set_entity_ai_type(enemy_entity, "simple")
    ai = controller.get_ai_for_entity(enemy_entity)
    assert isinstance(ai, SimplePathfindingAI)
