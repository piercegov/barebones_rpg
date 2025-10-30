"""AI systems for entities.

This module provides AI behavior for NPCs and enemies, including
pathfinding-based movement and decision making.
"""

from typing import Optional, Callable, Any
from barebones_rpg.entities.entity import Entity, Enemy
from barebones_rpg.world.world import Location
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder


class SimplePathfindingAI:
    """Simple pathfinding-based AI for enemies.
    
    This AI will:
    - Move toward a target using pathfinding
    - Attack if adjacent to target
    - Spend available action points efficiently
    
    Args:
        pathfinder: The pathfinder to use for navigation
    """
    
    def __init__(self, pathfinder: TilemapPathfinder):
        """Initialize the AI.
        
        Args:
            pathfinder: The pathfinder to use for navigation
        """
        self.pathfinder = pathfinder
    
    def process_turn(
        self,
        entity: Entity,
        target: Entity,
        location: Location,
        max_moves: int,
        on_attack: Optional[Callable[[Entity, Entity], None]] = None,
        attack_range: int = 1
    ) -> bool:
        """Process a turn for an entity using pathfinding AI.
        
        The AI will:
        1. Check if target is in attack range
        2. If yes, trigger attack callback
        3. If no, move toward target up to max_moves
        
        Args:
            entity: The entity performing actions
            target: The target entity
            location: The location/map
            max_moves: Maximum number of moves to make
            on_attack: Callback when entity attacks (entity, target)
            attack_range: Range required for attack (Manhattan distance)
            
        Returns:
            True if entity attacked, False if entity moved/did nothing
        """
        # Check if adjacent to target
        ex, ey = entity.position
        tx, ty = target.position
        distance = abs(ex - tx) + abs(ey - ty)
        
        if distance <= attack_range:
            # In attack range - attack!
            if on_attack:
                on_attack(entity, target)
            return True
        
        # Move toward target
        moves_made = 0
        while moves_made < max_moves:
            # Calculate path to target
            path = self.pathfinder.find_path(entity.position, target.position)
            
            if not path or len(path) <= 1:
                # No path or already at position
                break
            
            # Move one step along path
            next_pos = path[1]  # path[0] is current position
            
            # Check if tile is walkable and not occupied
            if not location.is_walkable(next_pos[0], next_pos[1]):
                break
            
            entity_at_pos = location.get_entity_at(next_pos[0], next_pos[1])
            
            if entity_at_pos is not None:
                # Tile is occupied, can't move there
                break
            
            # Move entity
            location.remove_entity(entity)
            location.add_entity(entity, next_pos[0], next_pos[1])
            entity.position = next_pos
            moves_made += 1
            
            # Check if now in attack range
            new_distance = abs(next_pos[0] - tx) + abs(next_pos[1] - ty)
            if new_distance <= attack_range:
                # Now in range - attack!
                if on_attack:
                    on_attack(entity, target)
                return True
        
        return False


class TacticalAI:
    """More advanced tactical AI with behavior modes.
    
    This AI can:
    - Chase and attack
    - Flee when low health
    - Patrol between points
    - Guard a specific location
    
    Args:
        pathfinder: The pathfinder to use for navigation
    """
    
    def __init__(self, pathfinder: TilemapPathfinder):
        """Initialize the tactical AI.
        
        Args:
            pathfinder: The pathfinder to use for navigation
        """
        self.pathfinder = pathfinder
        self.behavior_mode = "aggressive"  # aggressive, defensive, patrol, guard
        self.flee_hp_threshold = 0.3  # Flee when below 30% HP
    
    def should_flee(self, entity: Entity) -> bool:
        """Check if entity should flee based on HP.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if entity should flee
        """
        if not hasattr(entity, 'stats'):
            return False
        
        hp_percent = entity.stats.hp / entity.stats.max_hp
        return hp_percent < self.flee_hp_threshold
    
    def flee_from(
        self,
        entity: Entity,
        threat: Entity,
        location: Location,
        max_moves: int
    ):
        """Flee away from a threat.
        
        Args:
            entity: The entity fleeing
            threat: The entity to flee from
            location: The location/map
            max_moves: Maximum number of moves
        """
        ex, ey = entity.position
        tx, ty = threat.position
        
        # Calculate direction away from threat
        dx = ex - tx
        dy = ey - ty
        
        # Normalize direction
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        
        # Try to move away
        for _ in range(max_moves):
            # Try to move in the away direction
            new_x = ex + dx
            new_y = ey + dy
            
            # Check if valid position
            if (location.is_walkable(new_x, new_y) and 
                location.get_entity_at(new_x, new_y) is None):
                location.remove_entity(entity)
                location.add_entity(entity, new_x, new_y)
                entity.position = (new_x, new_y)
                ex, ey = new_x, new_y
            else:
                # Can't move in preferred direction, try alternatives
                break
    
    def process_turn(
        self,
        entity: Entity,
        target: Entity,
        location: Location,
        max_moves: int,
        on_attack: Optional[Callable[[Entity, Entity], None]] = None,
        attack_range: int = 1
    ) -> bool:
        """Process a turn using tactical AI.
        
        Args:
            entity: The entity performing actions
            target: The target entity
            location: The location/map
            max_moves: Maximum number of moves to make
            on_attack: Callback when entity attacks
            attack_range: Range required for attack
            
        Returns:
            True if entity attacked
        """
        # Check if should flee
        if self.should_flee(entity):
            self.flee_from(entity, target, location, max_moves)
            return False
        
        # Otherwise, use aggressive AI
        simple_ai = SimplePathfindingAI(self.pathfinder)
        return simple_ai.process_turn(
            entity, target, location, max_moves, on_attack, attack_range
        )
    
    def set_behavior(
        self,
        mode: str,
        flee_threshold: Optional[float] = None
    ):
        """Set AI behavior mode.
        
        Args:
            mode: Behavior mode ("aggressive", "defensive", "patrol", "guard")
            flee_threshold: HP threshold for fleeing (0.0-1.0)
        """
        self.behavior_mode = mode
        if flee_threshold is not None:
            self.flee_hp_threshold = flee_threshold


class AIController:
    """Controller for managing multiple AI entities.
    
    This is useful for processing all enemy turns in sequence.
    
    Args:
        pathfinder: The pathfinder to use
        default_ai_type: Default AI type ("simple" or "tactical")
    """
    
    def __init__(
        self,
        pathfinder: TilemapPathfinder,
        default_ai_type: str = "simple"
    ):
        """Initialize the AI controller.
        
        Args:
            pathfinder: The pathfinder to use
            default_ai_type: Default AI type for entities
        """
        self.pathfinder = pathfinder
        self.default_ai_type = default_ai_type
        self.ai_instances = {}
    
    def get_ai_for_entity(self, entity: Entity):
        """Get or create AI instance for an entity.
        
        Args:
            entity: The entity to get AI for
            
        Returns:
            AI instance (SimplePathfindingAI or TacticalAI)
        """
        if entity.id not in self.ai_instances:
            if self.default_ai_type == "tactical":
                self.ai_instances[entity.id] = TacticalAI(self.pathfinder)
            else:
                self.ai_instances[entity.id] = SimplePathfindingAI(self.pathfinder)
        
        return self.ai_instances[entity.id]
    
    def process_entity_turn(
        self,
        entity: Entity,
        target: Entity,
        location: Location,
        max_moves: int,
        on_attack: Optional[Callable[[Entity, Entity], None]] = None
    ) -> bool:
        """Process a turn for an entity.
        
        Args:
            entity: The entity to process
            target: The target entity
            location: The location/map
            max_moves: Maximum moves for this turn
            on_attack: Callback when entity attacks
            
        Returns:
            True if entity attacked
        """
        ai = self.get_ai_for_entity(entity)
        return ai.process_turn(entity, target, location, max_moves, on_attack)
    
    def process_all_enemies(
        self,
        enemies: list[Entity],
        target: Entity,
        location: Location,
        max_moves_per_enemy: int,
        on_attack: Optional[Callable[[Entity, Entity], None]] = None
    ):
        """Process turns for all enemies.
        
        Args:
            enemies: List of enemy entities
            target: The target entity (usually player)
            location: The location/map
            max_moves_per_enemy: Max moves per enemy
            on_attack: Callback when an enemy attacks
        """
        for enemy in enemies:
            self.process_entity_turn(
                enemy,
                target,
                location,
                max_moves_per_enemy,
                on_attack
            )
    
    def set_entity_ai_type(self, entity: Entity, ai_type: str):
        """Set specific AI type for an entity.
        
        Args:
            entity: The entity to set AI for
            ai_type: AI type ("simple" or "tactical")
        """
        if ai_type == "tactical":
            self.ai_instances[entity.id] = TacticalAI(self.pathfinder)
        else:
            self.ai_instances[entity.id] = SimplePathfindingAI(self.pathfinder)

