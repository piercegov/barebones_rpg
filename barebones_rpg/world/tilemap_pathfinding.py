"""Tilemap-specific pathfinding utilities.

This module provides pathfinding algorithms specifically designed for tile-based maps.
These utilities work with the Location class and assume grid-based movement.

Note: These pathfinding utilities are designed specifically for tile-based games.
      For non-tile-based games, you'll need different pathfinding approaches.
"""

from typing import List, Tuple, Set, Optional
from collections import deque

from barebones_rpg.world.world import Location


class TilemapPathfinder:
    """Pathfinding utilities for tile-based maps.

    This class provides BFS pathfinding and flood-fill algorithms
    specifically designed for tile-based grid movement.

    Args:
        location: The tile-based Location to pathfind within
        allow_diagonal: Whether to allow diagonal movement (default: False)
    """

    def __init__(self, location: Location, allow_diagonal: bool = False):
        """Initialize the pathfinder.

        Args:
            location: The tile-based Location to pathfind within
            allow_diagonal: Whether to allow diagonal movement
        """
        self.location = location
        self.allow_diagonal = allow_diagonal

    def get_directions(self) -> List[Tuple[int, int]]:
        """Get movement directions based on diagonal setting.

        Returns:
            List of (dx, dy) tuples for movement directions
        """
        if self.allow_diagonal:
            return [
                (0, 1),
                (0, -1),
                (1, 0),
                (-1, 0),  # Cardinal
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),  # Diagonal
            ]
        else:
            return [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Cardinal only

    def get_manhattan_distance(
        self, pos1: Tuple[int, int], pos2: Tuple[int, int]
    ) -> int:
        """Calculate Manhattan distance between two tile positions.

        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)

        Returns:
            Manhattan distance (sum of absolute differences)
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        allow_occupied_goal: bool = True,
    ) -> List[Tuple[int, int]]:
        """Find shortest path from start to goal using BFS.

        Args:
            start: Starting tile position (x, y)
            goal: Goal tile position (x, y)
            allow_occupied_goal: Whether to allow pathing to an occupied tile

        Returns:
            List of positions from start to goal (inclusive), or empty list if no path
        """
        if start == goal:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}
        directions = self.get_directions()

        while queue:
            pos, path = queue.popleft()

            # Check all movement directions
            for dx, dy in directions:
                new_pos = (pos[0] + dx, pos[1] + dy)

                if new_pos in visited:
                    continue

                # Check if walkable
                if not self.location.is_walkable(new_pos[0], new_pos[1]):
                    continue

                # Check if occupied (allow goal to be occupied if specified)
                entity = self.location.get_entity_at(new_pos[0], new_pos[1])
                if entity is not None and not (allow_occupied_goal and new_pos == goal):
                    continue

                new_path = path + [new_pos]

                if new_pos == goal:
                    return new_path

                visited.add(new_pos)
                queue.append((new_pos, new_path))

        return []  # No path found

    def calculate_reachable_tiles(
        self, start: Tuple[int, int], max_distance: int, allow_occupied: bool = False
    ) -> Set[Tuple[int, int]]:
        """Calculate all tiles reachable within a distance using flood fill.

        This is useful for showing movement range, spell range, etc.

        Args:
            start: Starting tile position (x, y)
            max_distance: Maximum distance to flood fill
            allow_occupied: Whether occupied tiles block further flooding

        Returns:
            Set of reachable tile positions
        """
        if max_distance <= 0:
            return set()

        reachable = set()
        visited = {start: 0}  # position -> cost to reach
        queue = deque([(start, 0)])
        directions = self.get_directions()

        while queue:
            pos, cost = queue.popleft()

            # Check all movement directions
            for dx, dy in directions:
                new_pos = (pos[0] + dx, pos[1] + dy)
                new_cost = cost + 1

                # Check if within max distance
                if new_cost > max_distance:
                    continue

                # Check if already visited with lower cost
                if new_pos in visited and visited[new_pos] <= new_cost:
                    continue

                # Check if walkable
                if not self.location.is_walkable(new_pos[0], new_pos[1]):
                    continue

                # Check if occupied by entity
                entity = self.location.get_entity_at(new_pos[0], new_pos[1])

                visited[new_pos] = new_cost
                reachable.add(new_pos)

                # Only continue flooding if tile is not occupied (or if we allow occupied)
                if entity is None or allow_occupied:
                    queue.append((new_pos, new_cost))

        return reachable

    def get_neighbors(
        self, pos: Tuple[int, int], walkable_only: bool = True
    ) -> List[Tuple[int, int]]:
        """Get all neighboring tiles to a position.

        Args:
            pos: Tile position (x, y)
            walkable_only: Whether to only return walkable neighbors

        Returns:
            List of neighboring tile positions
        """
        neighbors = []
        directions = self.get_directions()

        for dx, dy in directions:
            new_pos = (pos[0] + dx, pos[1] + dy)

            # Check if within bounds
            if not (
                0 <= new_pos[0] < self.location.width
                and 0 <= new_pos[1] < self.location.height
            ):
                continue

            # Check if walkable if required
            if walkable_only and not self.location.is_walkable(new_pos[0], new_pos[1]):
                continue

            neighbors.append(new_pos)

        return neighbors
