"""Targeting and distance calculation utilities for combat.

This module provides optional helper functions for distance calculations
and target filtering. These are completely optional - games can use their
own distance calculations or ignore positioning entirely.
"""

from typing import Tuple, List, Any, Callable, Optional
import math


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calculate Manhattan (grid-based) distance between two positions.

    Manhattan distance is the sum of horizontal and vertical distances,
    useful for grid-based movement where diagonal movement isn't allowed
    or costs the same as orthogonal movement.

    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)

    Returns:
        Manhattan distance as integer

    Example:
        >>> manhattan_distance((0, 0), (3, 4))
        7
        >>> manhattan_distance((5, 5), (5, 8))
        3
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def euclidean_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """Calculate Euclidean (straight-line) distance between two positions.

    Euclidean distance is the straight-line distance between two points,
    useful for more realistic distance calculations or line-of-sight checks.

    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)

    Returns:
        Euclidean distance as float

    Example:
        >>> euclidean_distance((0, 0), (3, 4))
        5.0
        >>> euclidean_distance((0, 0), (1, 1))
        1.414...
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx * dx + dy * dy)


def chebyshev_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calculate Chebyshev distance between two positions.

    Chebyshev distance is the maximum of horizontal and vertical distances,
    useful for grid-based games where diagonal movement costs the same as
    orthogonal movement (8-directional movement).

    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)

    Returns:
        Chebyshev distance as integer

    Example:
        >>> chebyshev_distance((0, 0), (3, 4))
        4
        >>> chebyshev_distance((5, 5), (8, 7))
        3
    """
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


def is_in_range(
    source: Any,
    target: Any,
    range_value: int,
    distance_func: Callable[
        [Tuple[int, int], Tuple[int, int]], float
    ] = manhattan_distance,
) -> bool:
    """Check if a target is within range of the source.

    This is a helper function that checks if both entities have position
    attributes and calculates if the target is within the specified range.

    Args:
        source: Source entity (must have 'position' attribute)
        target: Target entity (must have 'position' attribute)
        range_value: Maximum range
        distance_func: Function to calculate distance (default: manhattan_distance)

    Returns:
        True if target is in range, False otherwise

    Example:
        >>> class Entity:
        ...     def __init__(self, pos):
        ...         self.position = pos
        >>> player = Entity((0, 0))
        >>> enemy = Entity((2, 0))
        >>> is_in_range(player, enemy, range_value=3)
        True
        >>> is_in_range(player, enemy, range_value=1)
        False
    """
    # Check if both entities have positions
    if not hasattr(source, "position") or not hasattr(target, "position"):
        return True  # If no positioning, assume always in range

    distance = distance_func(source.position, target.position)
    return distance <= range_value


def filter_targets_by_range(
    source: Any,
    targets: List[Any],
    range_value: int,
    distance_func: Callable[
        [Tuple[int, int], Tuple[int, int]], float
    ] = manhattan_distance,
) -> List[Any]:
    """Filter a list of targets to only those within range of the source.

    This is useful for AOE abilities that have a maximum range, or for
    validating that all selected targets are reachable.

    Args:
        source: Source entity (must have 'position' attribute)
        targets: List of potential target entities
        range_value: Maximum range
        distance_func: Function to calculate distance (default: manhattan_distance)

    Returns:
        Filtered list of targets within range

    Example:
        >>> class Entity:
        ...     def __init__(self, pos):
        ...         self.position = pos
        >>> player = Entity((0, 0))
        >>> enemies = [Entity((1, 0)), Entity((5, 0)), Entity((2, 1))]
        >>> in_range = filter_targets_by_range(player, enemies, range_value=3)
        >>> len(in_range)
        2
    """
    return [
        target
        for target in targets
        if is_in_range(source, target, range_value, distance_func)
    ]


def get_targets_in_area(
    center: Tuple[int, int],
    radius: int,
    all_entities: List[Any],
    distance_func: Callable[
        [Tuple[int, int], Tuple[int, int]], float
    ] = manhattan_distance,
) -> List[Any]:
    """Get all entities within a circular area.

    This is useful for AOE effects centered on a position rather than
    an entity (e.g., a fireball explosion at a location).

    Args:
        center: Center position (x, y)
        radius: Radius of the area
        all_entities: List of all entities to check
        distance_func: Function to calculate distance (default: manhattan_distance)

    Returns:
        List of entities within the area

    Example:
        >>> class Entity:
        ...     def __init__(self, pos):
        ...         self.position = pos
        >>> entities = [Entity((0, 0)), Entity((1, 1)), Entity((5, 5))]
        >>> targets = get_targets_in_area((0, 0), radius=2, all_entities=entities)
        >>> len(targets)
        2
    """
    result = []
    for entity in all_entities:
        if hasattr(entity, "position"):
            distance = distance_func(center, entity.position)
            if distance <= radius:
                result.append(entity)
    return result


def get_targets_in_line(
    start: Tuple[int, int],
    end: Tuple[int, int],
    all_entities: List[Any],
    width: int = 0,
) -> List[Any]:
    """Get all entities in a line between two points.

    This is useful for line-based AOE effects like beam attacks or
    penetrating shots. Uses Bresenham's line algorithm.

    Args:
        start: Starting position (x, y)
        end: Ending position (x, y)
        all_entities: List of all entities to check
        width: Width of the line (0 = single tile wide)

    Returns:
        List of entities along the line

    Example:
        >>> class Entity:
        ...     def __init__(self, pos):
        ...         self.position = pos
        >>> entities = [Entity((1, 0)), Entity((2, 0)), Entity((0, 1))]
        >>> targets = get_targets_in_line((0, 0), (3, 0), entities)
        >>> len(targets)
        2
    """
    # Get all tiles on the line using Bresenham's algorithm
    line_tiles = _bresenham_line(start, end)

    # If width > 0, expand the line
    if width > 0:
        expanded_tiles = set()
        for tile in line_tiles:
            for dx in range(-width, width + 1):
                for dy in range(-width, width + 1):
                    expanded_tiles.add((tile[0] + dx, tile[1] + dy))
        line_tiles = list(expanded_tiles)

    # Find entities on these tiles
    result = []
    for entity in all_entities:
        if hasattr(entity, "position") and entity.position in line_tiles:
            result.append(entity)

    return result


def _bresenham_line(
    start: Tuple[int, int], end: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Generate points along a line using Bresenham's algorithm.

    Args:
        start: Starting position (x, y)
        end: Ending position (x, y)

    Returns:
        List of positions along the line
    """
    x0, y0 = start
    x1, y1 = end
    points = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0
    while True:
        points.append((x, y))

        if x == x1 and y == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points
