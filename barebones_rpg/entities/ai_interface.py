"""AI interface system for entity behavior.

This module provides a flexible interface for implementing custom AI behavior
for NPCs and enemies. Users can implement their own AI using any approach:
state machines, behavior trees, LLM-based decision making, etc.

The registry pattern allows memory-efficient sharing of AI instances across
many entities.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Tuple, TYPE_CHECKING
from pydantic import BaseModel, Field

from ..core.registry import Registry

if TYPE_CHECKING:
    from .entity import Entity
    from ..world.world import World, Location


class AIContext(BaseModel):
    """Context information passed to AI for decision making.

    This provides all the information an AI needs to make decisions about
    what action to take. The context can be extended with custom data via
    the metadata field.

    Example:
        >>> context = AIContext(
        ...     entity=goblin,
        ...     nearby_entities=[player, other_goblin],
        ...     metadata={"last_attacked_by": player.id}
        ... )
    """

    entity: Any = Field(description="The entity making the decision")
    world: Optional[Any] = Field(default=None, description="The game world")
    location: Optional[Any] = Field(default=None, description="Current location/map")
    nearby_entities: List[Any] = Field(
        default_factory=list, description="Entities within perception range"
    )
    combat_context: Optional[Any] = Field(
        default=None, description="Combat system reference if in combat"
    )
    game_state: Optional[Any] = Field(
        default=None, description="Additional game state reference"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom context data"
    )

    model_config = {"arbitrary_types_allowed": True}


class AIAction(BaseModel):
    """Action decided by AI to be executed by game systems.

    The AI returns this to communicate what it wants to do. The game's
    combat/world systems are responsible for executing the action.

    Common action types:
    - "move": Move to target_position
    - "attack": Attack the target entity
    - "use_skill": Use a skill/ability (details in parameters)
    - "use_item": Use an item (details in parameters)
    - "wait": Do nothing this turn
    - "flee": Run away from target
    - "custom": Custom action (defined in parameters)

    Example:
        >>> # Move action
        >>> action = AIAction(
        ...     action_type="move",
        ...     target_position=(10, 5)
        ... )
        >>>
        >>> # Attack action
        >>> action = AIAction(
        ...     action_type="attack",
        ...     target=player
        ... )
        >>>
        >>> # Use skill action
        >>> action = AIAction(
        ...     action_type="use_skill",
        ...     target=player,
        ...     parameters={"skill_name": "fireball", "power": 50}
        ... )
    """

    action_type: str = Field(
        description="Type of action (move, attack, use_skill, wait, custom, etc.)"
    )
    target: Optional[Any] = Field(
        default=None, description="Target entity for the action"
    )
    target_position: Optional[Tuple[int, int]] = Field(
        default=None, description="Target position for movement"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional action parameters"
    )

    model_config = {"arbitrary_types_allowed": True}


class AIInterface(ABC):
    """Base interface for entity AI implementations.

    This is the core interface that all AI implementations must follow.
    Users can implement this to create custom AI behavior using any approach:
    - Simple state machines
    - Behavior trees
    - Utility-based AI
    - LLM-based decision making
    - Rule-based systems
    - Or any other approach

    The AI receives an AIContext with all relevant information and returns
    an AIAction describing what it wants to do. The game systems are responsible
    for executing the action.

    Example:
        >>> class AggressiveMeleeAI(AIInterface):
        ...     def decide_action(self, context: AIContext) -> Optional[AIAction]:
        ...         # Find nearest enemy
        ...         if context.nearby_entities:
        ...             target = context.nearby_entities[0]
        ...             # Check distance
        ...             if self._is_adjacent(context.entity, target):
        ...                 return AIAction(action_type="attack", target=target)
        ...             else:
        ...                 return AIAction(
        ...                     action_type="move",
        ...                     target_position=target.position
        ...                 )
        ...         return AIAction(action_type="wait")
    """

    @abstractmethod
    def decide_action(self, context: AIContext) -> Optional[AIAction]:
        """Decide what action to take based on the current context.

        This method is called by the game when it's the entity's turn to act.
        The AI should analyze the context and return an appropriate action.

        Args:
            context: Current game context with entity state and surroundings

        Returns:
            AIAction describing what to do, or None to do nothing

        Example:
            >>> def decide_action(self, context: AIContext) -> Optional[AIAction]:
            ...     entity = context.entity
            ...     if entity.stats.hp < entity.stats.max_hp * 0.3:
            ...         # Flee when low health
            ...         return AIAction(action_type="flee")
            ...     elif context.nearby_entities:
            ...         # Attack nearest enemy
            ...         target = context.nearby_entities[0]
            ...         return AIAction(action_type="attack", target=target)
            ...     return AIAction(action_type="wait")
        """
        pass


class AIRegistry(Registry[AIInterface]):
    """Global registry for AI behavior types.

    This registry allows sharing AI instances across many entities for
    memory efficiency. Register AI implementations once, then reference
    them by name in entity definitions.

    Example:
        >>> # Define and register AI
        >>> aggressive_ai = AggressiveMeleeAI()
        >>> AIRegistry.register("aggressive_melee", aggressive_ai)
        >>>
        >>> # Create entities that use the AI
        >>> goblin1 = Enemy(name="Goblin 1", ai_type="aggressive_melee")
        >>> goblin2 = Enemy(name="Goblin 2", ai_type="aggressive_melee")
        >>> # Both goblins share the same AI instance
        >>>
        >>> # Later, get AI for an entity
        >>> ai = AIRegistry.get(goblin1.ai_type)
        >>> if ai:
        ...     action = ai.decide_action(context)
    """

    _registry: Dict[str, AIInterface] = {}
