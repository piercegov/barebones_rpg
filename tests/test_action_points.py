"""Tests for Action Points system."""

import pytest
from barebones_rpg.world.action_points import APManager
from barebones_rpg.world.world import Location, Tile
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder
from barebones_rpg.entities.entity import Entity, Character, Enemy
from barebones_rpg.entities.stats import Stats


@pytest.fixture
def ap_manager():
    """Create a default AP manager."""
    return APManager(player_ap=5, enemy_ap=3, npc_ap=2, ap_cost_per_tile=1)


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
def player_entity():
    """Create a player entity."""
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Character(name="Hero", stats=stats)
    entity.position = (0, 0)
    return entity


@pytest.fixture
def enemy_entity():
    """Create an enemy entity."""
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Enemy(name="Goblin", stats=stats, exp_reward=10, gold_reward=5)
    entity.position = (5, 5)
    return entity


@pytest.fixture
def npc_entity():
    """Create an NPC entity."""
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Entity(name="NPC", stats=stats, faction="neutral")
    entity.position = (3, 3)
    return entity


def test_ap_manager_initialization():
    """Test AP manager initialization."""
    manager = APManager(player_ap=10, enemy_ap=5, npc_ap=3, ap_cost_per_tile=2)

    assert manager.default_ap["player"] == 10
    assert manager.default_ap["enemy"] == 5
    assert manager.default_ap["neutral"] == 3
    assert manager.ap_cost_per_tile == 2


def test_ap_manager_default_initialization():
    """Test AP manager with default values."""
    manager = APManager()

    assert manager.default_ap["player"] == 5
    assert manager.default_ap["enemy"] == 3
    assert manager.default_ap["neutral"] == 0


def test_get_default_ap_player(ap_manager, player_entity):
    """Test getting default AP for player."""
    ap = ap_manager.get_default_ap(player_entity)
    assert ap == 5


def test_get_default_ap_enemy(ap_manager, enemy_entity):
    """Test getting default AP for enemy."""
    ap = ap_manager.get_default_ap(enemy_entity)
    assert ap == 3


def test_get_default_ap_npc(ap_manager, npc_entity):
    """Test getting default AP for NPC."""
    ap = ap_manager.get_default_ap(npc_entity)
    assert ap == 2


def test_get_default_ap_unknown_faction(ap_manager):
    """Test getting default AP for unknown faction."""
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Entity(name="Unknown", stats=stats, faction="unknown")
    ap = ap_manager.get_default_ap(entity)
    assert ap == 0


def test_start_turn(ap_manager, player_entity):
    """Test starting a turn for an entity."""
    ap = ap_manager.start_turn(player_entity)

    assert ap == 5
    assert ap_manager.get_remaining_ap(player_entity) == 5
    assert ap_manager.current_turn_entity == player_entity.id


def test_start_turn_multiple_entities(ap_manager, player_entity, enemy_entity):
    """Test starting turns for multiple entities."""
    ap_manager.start_turn(player_entity)
    assert ap_manager.current_turn_entity == player_entity.id

    ap_manager.start_turn(enemy_entity)
    assert ap_manager.current_turn_entity == enemy_entity.id
    assert ap_manager.get_remaining_ap(enemy_entity) == 3


def test_get_remaining_ap_no_turn_started(ap_manager, player_entity):
    """Test getting remaining AP when no turn has started."""
    ap = ap_manager.get_remaining_ap(player_entity)
    assert ap == 0


def test_spend_ap_success(ap_manager, player_entity):
    """Test successfully spending AP."""
    ap_manager.start_turn(player_entity)

    success = ap_manager.spend_ap(player_entity, 2)
    assert success
    assert ap_manager.get_remaining_ap(player_entity) == 3


def test_spend_ap_all(ap_manager, player_entity):
    """Test spending all AP."""
    ap_manager.start_turn(player_entity)

    success = ap_manager.spend_ap(player_entity, 5)
    assert success
    assert ap_manager.get_remaining_ap(player_entity) == 0


def test_spend_ap_insufficient(ap_manager, player_entity):
    """Test spending more AP than available."""
    ap_manager.start_turn(player_entity)

    success = ap_manager.spend_ap(player_entity, 10)
    assert not success
    assert ap_manager.get_remaining_ap(player_entity) == 5


def test_spend_ap_exact_amount(ap_manager, player_entity):
    """Test spending exact amount of remaining AP."""
    ap_manager.start_turn(player_entity)
    ap_manager.spend_ap(player_entity, 3)

    success = ap_manager.spend_ap(player_entity, 2)
    assert success
    assert ap_manager.get_remaining_ap(player_entity) == 0


def test_calculate_valid_moves_basic(ap_manager, player_entity, simple_location):
    """Test calculating valid moves."""
    simple_location.add_entity(player_entity, 5, 5)
    player_entity.position = (5, 5)
    ap_manager.start_turn(player_entity)

    pathfinder = TilemapPathfinder(simple_location)
    valid_moves = ap_manager.calculate_valid_moves(
        player_entity, simple_location, pathfinder
    )

    # With 5 AP and cost of 1 per tile, should be able to move 5 tiles
    assert len(valid_moves) > 0
    # All moves should be reachable
    for move in valid_moves:
        distance = abs(move[0] - 5) + abs(move[1] - 5)
        assert distance <= 5


def test_calculate_valid_moves_no_ap(ap_manager, player_entity, simple_location):
    """Test calculating valid moves with no AP."""
    simple_location.add_entity(player_entity, 5, 5)
    player_entity.position = (5, 5)
    ap_manager.start_turn(player_entity)
    ap_manager.spend_ap(player_entity, 5)

    pathfinder = TilemapPathfinder(simple_location)
    valid_moves = ap_manager.calculate_valid_moves(
        player_entity, simple_location, pathfinder
    )

    assert len(valid_moves) == 0


def test_calculate_valid_moves_without_pathfinder(
    ap_manager, player_entity, simple_location
):
    """Test calculating valid moves without providing pathfinder."""
    simple_location.add_entity(player_entity, 5, 5)
    player_entity.position = (5, 5)
    ap_manager.start_turn(player_entity)

    # Should create pathfinder internally
    valid_moves = ap_manager.calculate_valid_moves(player_entity, simple_location)
    assert len(valid_moves) > 0


def test_calculate_movement_cost_simple_path(ap_manager):
    """Test calculating movement cost for simple path."""
    path = [(0, 0), (1, 0), (2, 0), (3, 0)]
    cost = ap_manager.calculate_movement_cost(path)

    assert cost == 3  # 4 tiles - 1 starting position


def test_calculate_movement_cost_single_tile(ap_manager):
    """Test calculating movement cost for single tile (no movement)."""
    path = [(0, 0)]
    cost = ap_manager.calculate_movement_cost(path)

    assert cost == 0


def test_calculate_movement_cost_empty_path(ap_manager):
    """Test calculating movement cost for empty path."""
    path = []
    cost = ap_manager.calculate_movement_cost(path)

    assert cost == 0


def test_calculate_movement_cost_custom_cost():
    """Test calculating movement cost with custom cost per tile."""
    manager = APManager(ap_cost_per_tile=2)
    path = [(0, 0), (1, 0), (2, 0)]
    cost = manager.calculate_movement_cost(path)

    assert cost == 4  # 2 moves * 2 cost per tile


def test_can_afford_move_yes(ap_manager, player_entity):
    """Test checking if entity can afford a move."""
    ap_manager.start_turn(player_entity)
    path = [(0, 0), (1, 0), (2, 0)]  # Cost: 2

    can_afford = ap_manager.can_afford_move(player_entity, path)
    assert can_afford


def test_can_afford_move_no(ap_manager, player_entity):
    """Test checking if entity cannot afford a move."""
    ap_manager.start_turn(player_entity)
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0)]  # Cost: 6

    can_afford = ap_manager.can_afford_move(player_entity, path)
    assert not can_afford


def test_can_afford_move_exact(ap_manager, player_entity):
    """Test checking if entity can afford move with exact AP."""
    ap_manager.start_turn(player_entity)
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]  # Cost: 5

    can_afford = ap_manager.can_afford_move(player_entity, path)
    assert can_afford


def test_process_movement_success(ap_manager, player_entity, simple_location):
    """Test processing a successful movement."""
    simple_location.add_entity(player_entity, 0, 0)
    player_entity.position = (0, 0)
    ap_manager.start_turn(player_entity)

    pathfinder = TilemapPathfinder(simple_location)
    success = ap_manager.process_movement(
        player_entity, simple_location, (3, 0), pathfinder
    )

    assert success
    assert player_entity.position == (3, 0)
    assert ap_manager.get_remaining_ap(player_entity) == 2  # 5 - 3


def test_process_movement_insufficient_ap(ap_manager, player_entity, simple_location):
    """Test processing movement with insufficient AP."""
    simple_location.add_entity(player_entity, 0, 0)
    player_entity.position = (0, 0)
    ap_manager.start_turn(player_entity)

    pathfinder = TilemapPathfinder(simple_location)
    success = ap_manager.process_movement(
        player_entity, simple_location, (7, 0), pathfinder
    )

    assert not success
    assert player_entity.position == (0, 0)  # Didn't move


def test_process_movement_no_path(ap_manager, player_entity, simple_location):
    """Test processing movement with no valid path."""
    # Block the path
    for x in range(10):
        simple_location.set_tile(x, 1, Tile(x=x, y=1, tile_type="wall", walkable=False))

    simple_location.add_entity(player_entity, 0, 0)
    player_entity.position = (0, 0)
    ap_manager.start_turn(player_entity)

    pathfinder = TilemapPathfinder(simple_location)
    success = ap_manager.process_movement(
        player_entity, simple_location, (5, 5), pathfinder
    )

    assert not success


def test_process_movement_with_callback(ap_manager, player_entity, simple_location):
    """Test processing movement with callback."""
    simple_location.add_entity(player_entity, 0, 0)
    player_entity.position = (0, 0)
    ap_manager.start_turn(player_entity)

    callback_called = []

    def on_move(entity, old_pos, new_pos):
        callback_called.append((entity, old_pos, new_pos))

    pathfinder = TilemapPathfinder(simple_location)
    success = ap_manager.process_movement(
        player_entity, simple_location, (2, 0), pathfinder, on_move=on_move
    )

    assert success
    assert len(callback_called) == 1
    assert callback_called[0][0] == player_entity
    assert callback_called[0][1] == (0, 0)
    assert callback_called[0][2] == (2, 0)


def test_process_movement_without_pathfinder(
    ap_manager, player_entity, simple_location
):
    """Test processing movement without providing pathfinder."""
    simple_location.add_entity(player_entity, 0, 0)
    player_entity.position = (0, 0)
    ap_manager.start_turn(player_entity)

    # Should create pathfinder internally
    success = ap_manager.process_movement(player_entity, simple_location, (2, 0))

    assert success
    assert player_entity.position == (2, 0)


def test_has_ap_remaining_true(ap_manager, player_entity):
    """Test checking if entity has AP remaining."""
    ap_manager.start_turn(player_entity)

    assert ap_manager.has_ap_remaining(player_entity)


def test_has_ap_remaining_false(ap_manager, player_entity):
    """Test checking if entity has no AP remaining."""
    ap_manager.start_turn(player_entity)
    ap_manager.spend_ap(player_entity, 5)

    assert not ap_manager.has_ap_remaining(player_entity)


def test_has_ap_remaining_no_turn(ap_manager, player_entity):
    """Test checking AP when no turn has started."""
    assert not ap_manager.has_ap_remaining(player_entity)


def test_end_turn(ap_manager, player_entity):
    """Test ending a turn."""
    ap_manager.start_turn(player_entity)
    ap_manager.spend_ap(player_entity, 2)

    ap_manager.end_turn(player_entity)

    assert ap_manager.get_remaining_ap(player_entity) == 0
    assert ap_manager.current_turn_entity is None


def test_end_turn_different_entity(ap_manager, player_entity, enemy_entity):
    """Test ending turn for different entity than current."""
    ap_manager.start_turn(player_entity)
    ap_manager.end_turn(enemy_entity)

    # Current turn entity should not change
    assert ap_manager.current_turn_entity == player_entity.id


def test_reset(ap_manager, player_entity, enemy_entity):
    """Test resetting all AP tracking."""
    ap_manager.start_turn(player_entity)
    ap_manager.start_turn(enemy_entity)

    ap_manager.reset()

    assert ap_manager.get_remaining_ap(player_entity) == 0
    assert ap_manager.get_remaining_ap(enemy_entity) == 0
    assert ap_manager.current_turn_entity is None


def test_multiple_turns_same_entity(ap_manager, player_entity):
    """Test starting multiple turns for same entity."""
    ap_manager.start_turn(player_entity)
    ap_manager.spend_ap(player_entity, 3)

    # Start new turn - should reset AP
    ap_manager.start_turn(player_entity)
    assert ap_manager.get_remaining_ap(player_entity) == 5
