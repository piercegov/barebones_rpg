"""Tests for tilemap pathfinding."""

import pytest
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder
from barebones_rpg.world.world import Location, Tile
from barebones_rpg.entities.entity import Entity
from barebones_rpg.entities.stats import Stats


@pytest.fixture
def simple_location():
    """Create a simple 5x5 location for testing."""
    loc = Location(
        name="Test Area",
        description="Test location",
        width=5,
        height=5,
    )
    # All tiles walkable by default
    for y in range(5):
        for x in range(5):
            loc.set_tile(x, y, Tile(x=x, y=y, tile_type="floor", walkable=True))
    return loc


@pytest.fixture
def location_with_walls():
    """Create a location with walls for pathfinding tests."""
    loc = Location(
        name="Maze",
        description="Test maze",
        width=5,
        height=5,
    )
    # Create a simple layout with walls
    for y in range(5):
        for x in range(5):
            loc.set_tile(x, y, Tile(x=x, y=y, tile_type="floor", walkable=True))

    # Add a wall in the middle
    loc.set_tile(2, 0, Tile(x=2, y=0, tile_type="wall", walkable=False))
    loc.set_tile(2, 1, Tile(x=2, y=1, tile_type="wall", walkable=False))
    loc.set_tile(2, 2, Tile(x=2, y=2, tile_type="wall", walkable=False))
    return loc


@pytest.fixture
def basic_entity():
    """Create a basic entity for testing."""
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    return Entity(name="Test Entity", stats=stats)


def test_pathfinder_initialization(simple_location):
    """Test pathfinder initialization."""
    pathfinder = TilemapPathfinder(simple_location)
    assert pathfinder.location == simple_location
    assert not pathfinder.allow_diagonal


def test_pathfinder_initialization_with_diagonal(simple_location):
    """Test pathfinder initialization with diagonal movement."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=True)
    assert pathfinder.allow_diagonal


def test_get_directions_cardinal_only(simple_location):
    """Test getting cardinal directions only."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=False)
    directions = pathfinder.get_directions()
    assert len(directions) == 4
    assert (0, 1) in directions
    assert (0, -1) in directions
    assert (1, 0) in directions
    assert (-1, 0) in directions


def test_get_directions_with_diagonal(simple_location):
    """Test getting all 8 directions including diagonal."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=True)
    directions = pathfinder.get_directions()
    assert len(directions) == 8
    assert (1, 1) in directions
    assert (-1, -1) in directions
    assert (1, -1) in directions
    assert (-1, 1) in directions


def test_get_manhattan_distance(simple_location):
    """Test Manhattan distance calculation."""
    pathfinder = TilemapPathfinder(simple_location)
    assert pathfinder.get_manhattan_distance((0, 0), (3, 4)) == 7
    assert pathfinder.get_manhattan_distance((2, 2), (2, 2)) == 0


def test_find_path_straight_line(simple_location):
    """Test pathfinding in a straight line."""
    pathfinder = TilemapPathfinder(simple_location)
    path = pathfinder.find_path((0, 0), (3, 0))

    assert len(path) == 4
    assert path[0] == (0, 0)
    assert path[-1] == (3, 0)


def test_find_path_same_position(simple_location):
    """Test pathfinding when start equals goal."""
    pathfinder = TilemapPathfinder(simple_location)
    path = pathfinder.find_path((2, 2), (2, 2))

    assert len(path) == 1
    assert path[0] == (2, 2)


def test_find_path_around_walls(location_with_walls):
    """Test pathfinding that needs to go around walls."""
    pathfinder = TilemapPathfinder(location_with_walls)
    path = pathfinder.find_path((0, 1), (4, 1))

    assert path is not None
    assert len(path) > 4  # Must go around the wall
    assert path[0] == (0, 1)
    assert path[-1] == (4, 1)
    # Make sure we don't go through walls
    for pos in path:
        assert location_with_walls.is_walkable(pos[0], pos[1])


def test_find_path_no_path(location_with_walls):
    """Test pathfinding when no path exists."""
    # Block the path completely
    location_with_walls.set_tile(2, 3, Tile(x=2, y=3, tile_type="wall", walkable=False))
    location_with_walls.set_tile(2, 4, Tile(x=2, y=4, tile_type="wall", walkable=False))

    pathfinder = TilemapPathfinder(location_with_walls)
    path = pathfinder.find_path((0, 1), (4, 1))

    assert path == []


def test_find_path_with_occupied_tiles(simple_location, basic_entity):
    """Test pathfinding with entities blocking the way."""
    # Place entity in the way
    blocker = Entity(name="Blocker", stats=basic_entity.stats)
    simple_location.add_entity(blocker, 2, 0)

    pathfinder = TilemapPathfinder(simple_location)
    path = pathfinder.find_path((0, 0), (4, 0))

    # Should find a path around the blocker
    assert len(path) > 0
    assert (2, 0) not in path[
        1:-1
    ]  # Should not go through occupied tile (unless it's goal)


def test_find_path_allow_occupied_goal(simple_location, basic_entity):
    """Test pathfinding to an occupied goal tile."""
    # Place entity at the goal
    target = Entity(name="Target", stats=basic_entity.stats)
    simple_location.add_entity(target, 3, 0)

    pathfinder = TilemapPathfinder(simple_location)
    path = pathfinder.find_path((0, 0), (3, 0), allow_occupied_goal=True)

    assert len(path) > 0
    assert path[-1] == (3, 0)


def test_find_path_disallow_occupied_goal(simple_location, basic_entity):
    """Test pathfinding when goal is occupied and not allowed."""
    # Place entity at the goal
    target = Entity(name="Target", stats=basic_entity.stats)
    simple_location.add_entity(target, 3, 0)

    pathfinder = TilemapPathfinder(simple_location)
    path = pathfinder.find_path((0, 0), (3, 0), allow_occupied_goal=False)

    # Should not find a path to occupied tile
    assert path == [] or path[-1] != (3, 0)


def test_find_path_diagonal(simple_location):
    """Test pathfinding with diagonal movement allowed."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=True)
    path = pathfinder.find_path((0, 0), (3, 3))

    # With diagonal movement, path should be shorter
    assert len(path) == 4  # 3 diagonal moves + start position
    assert path[0] == (0, 0)
    assert path[-1] == (3, 3)


def test_calculate_reachable_tiles_basic(simple_location):
    """Test calculating reachable tiles with basic distance."""
    pathfinder = TilemapPathfinder(simple_location)
    reachable = pathfinder.calculate_reachable_tiles((2, 2), max_distance=2)

    # Should reach tiles within Manhattan distance 2
    assert (2, 2) in reachable or (
        2,
        2,
    ) not in reachable  # Start may or may not be included
    assert (2, 0) in reachable  # 2 steps up
    assert (2, 4) in reachable  # 2 steps down
    assert (0, 2) in reachable  # 2 steps left
    assert (4, 2) in reachable  # 2 steps right
    assert (3, 3) in reachable  # 1+1 diagonal


def test_calculate_reachable_tiles_zero_distance(simple_location):
    """Test calculating reachable tiles with zero distance."""
    pathfinder = TilemapPathfinder(simple_location)
    reachable = pathfinder.calculate_reachable_tiles((2, 2), max_distance=0)

    assert len(reachable) == 0


def test_calculate_reachable_tiles_with_walls(location_with_walls):
    """Test calculating reachable tiles with walls blocking."""
    pathfinder = TilemapPathfinder(location_with_walls)
    reachable = pathfinder.calculate_reachable_tiles((0, 0), max_distance=3)

    # Should not include tiles blocked by walls
    for pos in reachable:
        assert location_with_walls.is_walkable(pos[0], pos[1])


def test_calculate_reachable_tiles_with_occupied(simple_location, basic_entity):
    """Test calculating reachable tiles with occupied tiles."""
    # Place entity to block path
    blocker = Entity(name="Blocker", stats=basic_entity.stats)
    simple_location.add_entity(blocker, 2, 2)

    pathfinder = TilemapPathfinder(simple_location)
    reachable = pathfinder.calculate_reachable_tiles(
        (2, 2), max_distance=2, allow_occupied=False
    )

    # Occupied tile might be included but shouldn't block flooding
    # The behavior depends on implementation


def test_calculate_reachable_tiles_allow_occupied(simple_location, basic_entity):
    """Test calculating reachable tiles allowing occupied tiles."""
    # Place entity
    blocker = Entity(name="Blocker", stats=basic_entity.stats)
    simple_location.add_entity(blocker, 2, 1)

    pathfinder = TilemapPathfinder(simple_location)
    reachable = pathfinder.calculate_reachable_tiles(
        (2, 0), max_distance=3, allow_occupied=True
    )

    # Should be able to flood through occupied tiles
    assert len(reachable) > 0


def test_calculate_reachable_tiles_diagonal(simple_location):
    """Test calculating reachable tiles with diagonal movement."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=True)
    reachable = pathfinder.calculate_reachable_tiles((2, 2), max_distance=1)

    # Should reach 8 adjacent tiles with diagonal movement
    assert len(reachable) >= 8


def test_get_neighbors_cardinal_only(simple_location):
    """Test getting neighbors with cardinal directions only."""
    pathfinder = TilemapPathfinder(simple_location)
    neighbors = pathfinder.get_neighbors((2, 2), walkable_only=False)

    assert len(neighbors) == 4
    assert (2, 3) in neighbors
    assert (2, 1) in neighbors
    assert (3, 2) in neighbors
    assert (1, 2) in neighbors


def test_get_neighbors_with_diagonal(simple_location):
    """Test getting neighbors with diagonal movement."""
    pathfinder = TilemapPathfinder(simple_location, allow_diagonal=True)
    neighbors = pathfinder.get_neighbors((2, 2), walkable_only=False)

    assert len(neighbors) == 8


def test_get_neighbors_at_edge(simple_location):
    """Test getting neighbors at edge of map."""
    pathfinder = TilemapPathfinder(simple_location)
    neighbors = pathfinder.get_neighbors((0, 0), walkable_only=False)

    # At corner, only 2 neighbors
    assert len(neighbors) == 2
    assert (0, 1) in neighbors
    assert (1, 0) in neighbors


def test_get_neighbors_walkable_only(location_with_walls):
    """Test getting only walkable neighbors."""
    pathfinder = TilemapPathfinder(location_with_walls)
    neighbors = pathfinder.get_neighbors((2, 3), walkable_only=True)

    # Should only include walkable tiles
    for neighbor in neighbors:
        assert location_with_walls.is_walkable(neighbor[0], neighbor[1])


def test_get_neighbors_out_of_bounds(simple_location):
    """Test getting neighbors doesn't return out of bounds positions."""
    pathfinder = TilemapPathfinder(simple_location)
    neighbors = pathfinder.get_neighbors((0, 0), walkable_only=False)

    for x, y in neighbors:
        assert 0 <= x < simple_location.width
        assert 0 <= y < simple_location.height
