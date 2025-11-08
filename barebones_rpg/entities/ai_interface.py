"""AI interface system for entity behavior.

This module provides a flexible interface for implementing custom AI behavior
for NPCs and enemies. Users can implement their own AI using any approach:
state machines, behavior trees, LLM-based decision making, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .entity import Entity


class AIContext(BaseModel):
    """Context information for AI decision making.

    Provides common fields and a metadata dict for custom context.

    Example:
        >>> context = AIContext(
        ...     entity=goblin,
        ...     nearby_entities=[player, other_goblin],
        ...     metadata={"location": current_location, "combat": combat_instance}
        ... )
    """

    entity: Any = Field(description="The entity making the decision")
    nearby_entities: List[Any] = Field(
        default_factory=list, description="Entities within perception range"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom context data (location, combat, world, etc.)",
    )

    model_config = {"arbitrary_types_allowed": True}


class AIInterface(ABC):
    """Base interface for AI implementations.

    Implement decide_action() to create custom AI behavior.
    Users can implement this for any AI approach:
    - Simple state machines
    - Behavior trees
    - Utility-based AI
    - LLM-based decision making
    - Rule-based systems

    Example:
        >>> class AggressiveMeleeAI(AIInterface):
        ...     def decide_action(self, context: AIContext) -> dict:
        ...         if context.nearby_entities:
        ...             target = context.nearby_entities[0]
        ...             return {"action": "attack", "target": target}
        ...         return {"action": "wait"}
        >>>
        >>> goblin = Enemy(name="Goblin", ai=AggressiveMeleeAI())
    """

    @abstractmethod
    def decide_action(self, context: AIContext) -> dict:
        """Decide what action to take based on the current context.

        Args:
            context: AIContext with entity state and custom metadata

        Returns:
            Dict with "action" key and action-specific data.
            Common actions: "attack", "move", "use_skill", "use_item", "wait", "flee"

            Examples:
                {"action": "attack", "target": enemy}
                {"action": "move", "position": (10, 5)}
                {"action": "use_skill", "skill": "fireball", "target": enemy}
                {"action": "wait"}

        Example:
            >>> def decide_action(self, context: AIContext) -> dict:
            ...     entity = context.entity
            ...     if entity.stats.hp < entity.stats.max_hp * 0.3:
            ...         return {"action": "flee"}
            ...     elif context.nearby_entities:
            ...         target = context.nearby_entities[0]
            ...         return {"action": "attack", "target": target}
            ...     return {"action": "wait"}
        """
        pass
