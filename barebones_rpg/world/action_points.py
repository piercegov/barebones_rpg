"""Action Points (AP) system for turn-based tile movement.

This module provides an Action Points system commonly used in turn-based
tile-based RPGs where movement costs action points per tile.
"""

from typing import Optional, Set, Tuple, List, Dict, Any, Callable
from barebones_rpg.entities.entity import Entity
from barebones_rpg.world.world import Location
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder


class APManager:
    """Manages Action Points for turn-based movement.

    This class handles:
    - Tracking AP for entities
    - Calculating valid moves based on remaining AP
    - Processing movement with AP costs
    - Turn management

    Args:
        player_ap: Default AP for player entities (default: 5)
        enemy_ap: Default AP for enemy entities (default: 3)
        npc_ap: Default AP for NPC entities (default: 0)
        ap_cost_per_tile: AP cost to move one tile (default: 1)
    """

    def __init__(
        self,
        player_ap: int = 5,
        enemy_ap: int = 3,
        npc_ap: int = 0,
        ap_cost_per_tile: int = 1,
    ):
        """Initialize the AP manager."""
        self.default_ap = {"player": player_ap, "enemy": enemy_ap, "neutral": npc_ap}
        self.ap_cost_per_tile = ap_cost_per_tile
        self.current_ap: Dict[str, int] = {}  # entity_id -> current AP
        self.current_turn_entity: Optional[str] = None

    def get_default_ap(self, entity: Entity) -> int:
        """Get the default AP for an entity based on its faction.

        Args:
            entity: The entity to get default AP for

        Returns:
            Default AP value for the entity's faction
        """
        return self.default_ap.get(entity.faction, 0)

    def start_turn(self, entity: Entity) -> int:
        """Start a turn for an entity, resetting their AP.

        Args:
            entity: The entity starting their turn

        Returns:
            The entity's starting AP for this turn
        """
        ap = self.get_default_ap(entity)
        self.current_ap[entity.id] = ap
        self.current_turn_entity = entity.id
        return ap

    def get_remaining_ap(self, entity: Entity) -> int:
        """Get the remaining AP for an entity.

        Args:
            entity: The entity to check AP for

        Returns:
            Remaining AP (0 if entity has no AP tracked)
        """
        return self.current_ap.get(entity.id, 0)

    def spend_ap(self, entity: Entity, amount: int) -> bool:
        """Spend AP for an entity.

        Args:
            entity: The entity spending AP
            amount: Amount of AP to spend

        Returns:
            True if AP was spent, False if not enough AP
        """
        current = self.get_remaining_ap(entity)
        if current >= amount:
            self.current_ap[entity.id] = current - amount
            return True
        return False

    def calculate_valid_moves(
        self,
        entity: Entity,
        location: Location,
        pathfinder: Optional[TilemapPathfinder] = None,
    ) -> Set[Tuple[int, int]]:
        """Calculate all valid moves for an entity based on their remaining AP.

        Args:
            entity: The entity to calculate moves for
            location: The location/map the entity is on
            pathfinder: Optional pathfinder (will create one if not provided)

        Returns:
            Set of (x, y) positions the entity can move to
        """
        remaining_ap = self.get_remaining_ap(entity)
        max_distance = remaining_ap // self.ap_cost_per_tile

        if max_distance <= 0:
            return set()

        if pathfinder is None:
            pathfinder = TilemapPathfinder(location)

        # Use flood fill to find all reachable tiles
        return pathfinder.calculate_reachable_tiles(
            entity.position, max_distance, allow_occupied=False
        )

    def calculate_movement_cost(self, path: List[Tuple[int, int]]) -> int:
        """Calculate the AP cost for a movement path.

        Args:
            path: List of positions in the path (including start position)

        Returns:
            AP cost for the movement (excludes starting position)
        """
        if len(path) <= 1:
            return 0
        return (len(path) - 1) * self.ap_cost_per_tile

    def can_afford_move(self, entity: Entity, path: List[Tuple[int, int]]) -> bool:
        """Check if an entity can afford to move along a path.

        Args:
            entity: The entity attempting to move
            path: The movement path

        Returns:
            True if entity has enough AP for the move
        """
        cost = self.calculate_movement_cost(path)
        return self.get_remaining_ap(entity) >= cost

    def process_movement(
        self,
        entity: Entity,
        location: Location,
        target: Tuple[int, int],
        pathfinder: Optional[TilemapPathfinder] = None,
        on_move: Optional[
            Callable[[Entity, Tuple[int, int], Tuple[int, int]], None]
        ] = None,
    ) -> bool:
        """Process a movement for an entity, consuming AP.

        Args:
            entity: The entity moving
            location: The location/map the entity is on
            target: Target position to move to
            pathfinder: Optional pathfinder (will create one if not provided)
            on_move: Optional callback when movement succeeds (entity, old_pos, new_pos)

        Returns:
            True if movement was successful, False otherwise
        """
        if pathfinder is None:
            pathfinder = TilemapPathfinder(location)

        # Find path
        path = pathfinder.find_path(entity.position, target)

        if not path:
            return False

        # Check if we can afford the move
        if not self.can_afford_move(entity, path):
            return False

        # Calculate and spend AP
        cost = self.calculate_movement_cost(path)
        if not self.spend_ap(entity, cost):
            return False

        # Execute move
        old_pos = entity.position
        location.remove_entity(entity)
        location.add_entity(entity, target[0], target[1])
        entity.position = target

        # Trigger callback
        if on_move:
            on_move(entity, old_pos, target)

        return True

    def has_ap_remaining(self, entity: Entity) -> bool:
        """Check if an entity has any AP remaining.

        Args:
            entity: The entity to check

        Returns:
            True if entity has AP remaining
        """
        return self.get_remaining_ap(entity) > 0

    def end_turn(self, entity: Entity):
        """End the turn for an entity.

        Args:
            entity: The entity ending their turn
        """
        self.current_ap[entity.id] = 0
        if self.current_turn_entity == entity.id:
            self.current_turn_entity = None

    def reset(self):
        """Reset all AP tracking (useful for starting a new encounter)."""
        self.current_ap.clear()
        self.current_turn_entity = None
