"""Tests for combat targeting and distance utilities."""

import pytest
from barebones_rpg.combat.targeting import (
    manhattan_distance,
    euclidean_distance,
    chebyshev_distance,
    is_in_range,
    filter_targets_by_range,
    get_targets_in_area,
    get_targets_in_line,
    _bresenham_line,
)
from barebones_rpg.entities.entity import Entity
from barebones_rpg.entities.stats import Stats


class MockEntity:
    """Mock entity with position for testing."""

    def __init__(self, pos):
        self.position = pos


class MockEntityNoPos:
    """Mock entity without position for testing."""

    pass


def test_manhattan_distance_basic():
    """Test basic Manhattan distance calculation."""
    assert manhattan_distance((0, 0), (3, 4)) == 7
    assert manhattan_distance((5, 5), (5, 8)) == 3
    assert manhattan_distance((0, 0), (0, 0)) == 0


def test_manhattan_distance_negative_coords():
    """Test Manhattan distance with negative coordinates."""
    assert manhattan_distance((-3, -4), (3, 4)) == 14
    assert manhattan_distance((0, 0), (-5, -5)) == 10


def test_euclidean_distance_basic():
    """Test basic Euclidean distance calculation."""
    assert euclidean_distance((0, 0), (3, 4)) == 5.0
    assert euclidean_distance((0, 0), (0, 0)) == 0.0


def test_euclidean_distance_diagonal():
    """Test Euclidean distance for diagonal movement."""
    result = euclidean_distance((0, 0), (1, 1))
    assert abs(result - 1.414) < 0.01


def test_euclidean_distance_negative_coords():
    """Test Euclidean distance with negative coordinates."""
    assert euclidean_distance((-3, 0), (3, 0)) == 6.0
    result = euclidean_distance((-1, -1), (1, 1))
    assert abs(result - 2.828) < 0.01


def test_chebyshev_distance_basic():
    """Test basic Chebyshev distance calculation."""
    assert chebyshev_distance((0, 0), (3, 4)) == 4
    assert chebyshev_distance((5, 5), (8, 7)) == 3
    assert chebyshev_distance((0, 0), (0, 0)) == 0


def test_chebyshev_distance_negative_coords():
    """Test Chebyshev distance with negative coordinates."""
    assert chebyshev_distance((-5, -5), (5, 5)) == 10
    assert chebyshev_distance((0, 0), (-3, 4)) == 4


def test_chebyshev_distance_diagonal():
    """Test Chebyshev distance for diagonal movement (should be same as straight)."""
    assert chebyshev_distance((0, 0), (3, 3)) == 3


def test_is_in_range_basic():
    """Test basic range checking."""
    player = MockEntity((0, 0))
    enemy = MockEntity((2, 0))

    assert is_in_range(player, enemy, range_value=3)
    assert is_in_range(player, enemy, range_value=2)
    assert not is_in_range(player, enemy, range_value=1)


def test_is_in_range_different_distance_funcs():
    """Test range checking with different distance functions."""
    player = MockEntity((0, 0))
    enemy = MockEntity((3, 4))

    # Manhattan: 7
    assert is_in_range(player, enemy, range_value=7, distance_func=manhattan_distance)
    assert not is_in_range(
        player, enemy, range_value=6, distance_func=manhattan_distance
    )

    # Euclidean: 5.0
    assert is_in_range(player, enemy, range_value=5, distance_func=euclidean_distance)
    assert not is_in_range(
        player, enemy, range_value=4, distance_func=euclidean_distance
    )

    # Chebyshev: 4
    assert is_in_range(player, enemy, range_value=4, distance_func=chebyshev_distance)
    assert not is_in_range(
        player, enemy, range_value=3, distance_func=chebyshev_distance
    )


def test_is_in_range_no_position():
    """Test range checking when entities have no position (should always return True)."""
    entity_no_pos1 = MockEntityNoPos()
    entity_no_pos2 = MockEntityNoPos()
    entity_with_pos = MockEntity((0, 0))

    assert is_in_range(entity_no_pos1, entity_no_pos2, range_value=1)
    assert is_in_range(entity_no_pos1, entity_with_pos, range_value=1)
    assert is_in_range(entity_with_pos, entity_no_pos1, range_value=1)


def test_filter_targets_by_range_basic():
    """Test filtering targets by range."""
    player = MockEntity((0, 0))
    enemies = [MockEntity((1, 0)), MockEntity((5, 0)), MockEntity((2, 1))]

    in_range = filter_targets_by_range(player, enemies, range_value=3)
    assert len(in_range) == 2
    assert enemies[0] in in_range
    assert enemies[2] in in_range
    assert enemies[1] not in in_range


def test_filter_targets_by_range_empty():
    """Test filtering with no targets in range."""
    player = MockEntity((0, 0))
    enemies = [MockEntity((10, 10)), MockEntity((20, 20))]

    in_range = filter_targets_by_range(player, enemies, range_value=5)
    assert len(in_range) == 0


def test_filter_targets_by_range_all_in_range():
    """Test filtering when all targets are in range."""
    player = MockEntity((0, 0))
    enemies = [MockEntity((1, 0)), MockEntity((0, 1)), MockEntity((1, 1))]

    in_range = filter_targets_by_range(player, enemies, range_value=10)
    assert len(in_range) == 3


def test_filter_targets_by_range_different_distance_funcs():
    """Test filtering with different distance functions."""
    player = MockEntity((0, 0))
    enemies = [MockEntity((3, 0)), MockEntity((0, 3)), MockEntity((2, 2))]

    # Manhattan
    manhattan_in_range = filter_targets_by_range(
        player, enemies, range_value=3, distance_func=manhattan_distance
    )
    assert len(manhattan_in_range) == 2

    # Euclidean
    euclidean_in_range = filter_targets_by_range(
        player, enemies, range_value=3, distance_func=euclidean_distance
    )
    assert len(euclidean_in_range) == 3


def test_get_targets_in_area_basic():
    """Test getting targets in circular area."""
    entities = [MockEntity((0, 0)), MockEntity((1, 1)), MockEntity((5, 5))]

    targets = get_targets_in_area((0, 0), radius=2, all_entities=entities)
    assert len(targets) == 2
    assert entities[0] in targets
    assert entities[1] in targets
    assert entities[2] not in targets


def test_get_targets_in_area_no_position():
    """Test area targeting with entities without positions."""
    entities = [MockEntity((0, 0)), MockEntityNoPos(), MockEntity((1, 1))]

    targets = get_targets_in_area((0, 0), radius=2, all_entities=entities)
    assert len(targets) == 2


def test_get_targets_in_area_different_distance_funcs():
    """Test area targeting with different distance functions."""
    entities = [MockEntity((2, 0)), MockEntity((0, 2)), MockEntity((1, 1))]

    # Manhattan: distance = 2, 2, 2
    manhattan_targets = get_targets_in_area(
        (0, 0), radius=2, all_entities=entities, distance_func=manhattan_distance
    )
    assert len(manhattan_targets) == 3

    # Euclidean: distance = 2.0, 2.0, ~1.41
    euclidean_targets = get_targets_in_area(
        (0, 0), radius=1.5, all_entities=entities, distance_func=euclidean_distance
    )
    assert len(euclidean_targets) == 1
    assert entities[2] in euclidean_targets


def test_get_targets_in_area_empty():
    """Test area targeting with no targets in area."""
    entities = [MockEntity((10, 10)), MockEntity((20, 20))]

    targets = get_targets_in_area((0, 0), radius=3, all_entities=entities)
    assert len(targets) == 0


def test_bresenham_line_horizontal():
    """Test Bresenham's line algorithm for horizontal line."""
    line = _bresenham_line((0, 0), (3, 0))
    assert len(line) == 4
    assert (0, 0) in line
    assert (1, 0) in line
    assert (2, 0) in line
    assert (3, 0) in line


def test_bresenham_line_vertical():
    """Test Bresenham's line algorithm for vertical line."""
    line = _bresenham_line((0, 0), (0, 3))
    assert len(line) == 4
    assert (0, 0) in line
    assert (0, 1) in line
    assert (0, 2) in line
    assert (0, 3) in line


def test_bresenham_line_diagonal():
    """Test Bresenham's line algorithm for diagonal line."""
    line = _bresenham_line((0, 0), (3, 3))
    assert len(line) == 4
    assert (0, 0) in line
    assert (3, 3) in line


def test_bresenham_line_backwards():
    """Test Bresenham's line algorithm when going from end to start."""
    line1 = _bresenham_line((0, 0), (3, 0))
    line2 = _bresenham_line((3, 0), (0, 0))

    assert len(line1) == len(line2)


def test_bresenham_line_single_point():
    """Test Bresenham's line algorithm with same start and end."""
    line = _bresenham_line((2, 2), (2, 2))
    assert len(line) == 1
    assert line[0] == (2, 2)


def test_get_targets_in_line_basic():
    """Test getting targets in a line."""
    entities = [MockEntity((1, 0)), MockEntity((2, 0)), MockEntity((0, 1))]

    targets = get_targets_in_line((0, 0), (3, 0), entities)
    assert len(targets) == 2
    assert entities[0] in targets
    assert entities[1] in targets
    assert entities[2] not in targets


def test_get_targets_in_line_with_width():
    """Test getting targets in a line with width."""
    entities = [
        MockEntity((1, 0)),  # On line
        MockEntity((2, 0)),  # On line
        MockEntity((1, 1)),  # Adjacent to line
        MockEntity((0, 5)),  # Far away
    ]

    # Width 0 (single tile wide)
    targets_width_0 = get_targets_in_line((0, 0), (3, 0), entities, width=0)
    assert len(targets_width_0) == 2

    # Width 1 (3 tiles wide)
    targets_width_1 = get_targets_in_line((0, 0), (3, 0), entities, width=1)
    assert len(targets_width_1) == 3


def test_get_targets_in_line_no_position():
    """Test line targeting with entities without positions."""
    entities = [MockEntity((1, 0)), MockEntityNoPos(), MockEntity((2, 0))]

    targets = get_targets_in_line((0, 0), (3, 0), entities)
    assert len(targets) == 2


def test_get_targets_in_line_empty():
    """Test line targeting with no targets on line."""
    entities = [MockEntity((0, 5)), MockEntity((5, 5))]

    targets = get_targets_in_line((0, 0), (3, 0), entities)
    assert len(targets) == 0


def test_get_targets_in_line_diagonal():
    """Test line targeting with diagonal line."""
    entities = [MockEntity((1, 1)), MockEntity((2, 2)), MockEntity((3, 0))]

    targets = get_targets_in_line((0, 0), (3, 3), entities)
    assert entities[0] in targets
    assert entities[1] in targets
    assert entities[2] not in targets


def test_get_targets_in_line_vertical():
    """Test line targeting with vertical line."""
    entities = [MockEntity((0, 1)), MockEntity((0, 2)), MockEntity((1, 1))]

    targets = get_targets_in_line((0, 0), (0, 3), entities)
    assert len(targets) == 2
    assert entities[0] in targets
    assert entities[1] in targets
    assert entities[2] not in targets
