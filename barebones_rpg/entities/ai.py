"""AI systems for entities.

This module provides AI behavior for NPCs and enemies, including
pathfinding-based movement and decision making using the AIInterface.
"""

from typing import Optional, Dict, Any
from barebones_rpg.entities.entity import Entity
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder
from barebones_rpg.entities.ai_interface import AIInterface, AIContext


class SimplePathfindingAI(AIInterface):
    """Simple pathfinding-based AI for enemies.

    This AI will:
    - Move toward a target using pathfinding
    - Attack if adjacent to target
    - Spend available action points efficiently

    Args:
        pathfinder: The pathfinder to use for navigation
        attack_range: Range at which entity can attack (default: 1)
        max_moves: Maximum moves per turn (default: 3)
    """

    def __init__(
        self, pathfinder: TilemapPathfinder, attack_range: int = 1, max_moves: int = 3
    ):
        """Initialize the AI.

        Args:
            pathfinder: The pathfinder to use for navigation
            attack_range: Range at which entity can attack
            max_moves: Maximum moves per turn
        """
        self.pathfinder = pathfinder
        self.attack_range = attack_range
        self.max_moves = max_moves

    def decide_action(self, context: AIContext) -> dict:
        """Decide what action to take based on context.

        This implementation:
        1. Finds nearest enemy in nearby_entities
        2. If in attack range, returns attack action
        3. If not in range, returns move action toward target
        4. If no enemies nearby, returns wait action

        Args:
            context: AI context with entity and surroundings

        Returns:
            Dict with action information
        """
        entity = context.entity
        location = context.metadata.get("location")

        if not context.nearby_entities:
            return {"action": "wait"}

        target = context.nearby_entities[0]

        ex, ey = entity.position
        tx, ty = target.position
        distance = abs(ex - tx) + abs(ey - ty)

        if distance <= self.attack_range:
            return {"action": "attack", "target": target}

        if not location:
            return {"action": "wait"}

        path = self.pathfinder.find_path(entity.position, target.position)

        if not path or len(path) <= 1:
            return {"action": "wait"}

        next_pos = path[1]

        if not location.is_walkable(next_pos[0], next_pos[1]):
            return {"action": "wait"}

        entity_at_pos = location.get_entity_at(next_pos[0], next_pos[1])
        if entity_at_pos is not None:
            return {"action": "wait"}

        return {
            "action": "move",
            "position": next_pos,
            "max_moves": self.max_moves,
        }


class TacticalAI(AIInterface):
    """More advanced tactical AI with behavior modes.

    This AI can:
    - Chase and attack
    - Flee when low health
    - Patrol between points
    - Guard a specific location

    Args:
        pathfinder: The pathfinder to use for navigation
        flee_hp_threshold: HP percentage threshold for fleeing (default: 0.3)
        attack_range: Attack range (default: 1)
        max_moves: Maximum moves per turn (default: 3)
    """

    def __init__(
        self,
        pathfinder: TilemapPathfinder,
        flee_hp_threshold: float = 0.3,
        attack_range: int = 1,
        max_moves: int = 3,
    ):
        """Initialize the tactical AI.

        Args:
            pathfinder: The pathfinder to use for navigation
            flee_hp_threshold: HP percentage threshold for fleeing
            attack_range: Attack range
            max_moves: Maximum moves per turn
        """
        self.pathfinder = pathfinder
        self.behavior_mode = "aggressive"  # aggressive, defensive, patrol, guard
        self.flee_hp_threshold = flee_hp_threshold
        self.attack_range = attack_range
        self.max_moves = max_moves

    def decide_action(self, context: AIContext) -> dict:
        """Decide what action to take based on context.

        This implementation considers health status:
        - If HP below threshold, flees from nearest enemy
        - Otherwise, behaves like SimplePathfindingAI

        Args:
            context: AI context with entity and surroundings

        Returns:
            Dict with action information
        """
        entity = context.entity

        if self.should_flee(entity):
            if context.nearby_entities:
                threat = context.nearby_entities[0]
                return {
                    "action": "flee",
                    "target": threat,
                    "max_moves": self.max_moves,
                }
            return {"action": "wait"}

        simple_ai = SimplePathfindingAI(
            self.pathfinder, self.attack_range, self.max_moves
        )
        return simple_ai.decide_action(context)

    def should_flee(self, entity: Entity) -> bool:
        """Check if entity should flee based on HP.

        Args:
            entity: The entity to check

        Returns:
            True if entity should flee
        """
        if not hasattr(entity, "stats"):
            return False

        hp_percent = entity.stats.hp / entity.stats.max_hp
        return hp_percent < self.flee_hp_threshold

    def set_behavior(self, mode: str, flee_threshold: Optional[float] = None):
        """Set AI behavior mode.

        Args:
            mode: Behavior mode ("aggressive", "defensive", "patrol", "guard")
            flee_threshold: HP threshold for fleeing (0.0-1.0)
        """
        self.behavior_mode = mode
        if flee_threshold is not None:
            self.flee_hp_threshold = flee_threshold
