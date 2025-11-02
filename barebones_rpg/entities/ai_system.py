"""AI system for managing and executing entity AI.

This module provides helper classes for executing AI across entities,
making it easy to integrate AI into game loops and combat systems.
"""

from typing import List, Optional, Tuple, Callable, TYPE_CHECKING

from .ai_interface import AIInterface, AIContext, AIAction, AIRegistry

if TYPE_CHECKING:
    from .entity import Entity


class AISystem:
    """Helper system for managing and executing entity AI.

    This class provides convenient methods for:
    - Getting AI decisions for entities
    - Processing multiple entities at once
    - Building context for AI decision making

    Example:
        >>> ai_system = AISystem()
        >>>
        >>> # Process a single entity
        >>> context = AIContext(entity=goblin, nearby_entities=[player])
        >>> action = ai_system.process_entity(goblin, context)
        >>> if action and action.action_type == "attack":
        ...     combat.attack(goblin, action.target)
        >>>
        >>> # Process all enemies
        >>> for entity, action in ai_system.process_entities(enemies, make_context):
        ...     if action:
        ...         execute_action(entity, action)
    """

    def __init__(self):
        """Initialize the AI system."""
        self.registry = AIRegistry

    def get_ai(self, ai_type: str) -> Optional[AIInterface]:
        """Get an AI instance from the registry.

        Args:
            ai_type: Name of the AI type

        Returns:
            AI instance or None if not found
        """
        return self.registry.get(ai_type)

    def process_entity(
        self, entity: "Entity", context: AIContext
    ) -> Optional[AIAction]:
        """Get AI decision for a single entity.

        Args:
            entity: Entity to process
            context: Context for AI decision making

        Returns:
            AIAction describing what the entity wants to do, or None

        Example:
            >>> context = AIContext(
            ...     entity=goblin,
            ...     nearby_entities=[player],
            ...     location=current_location
            ... )
            >>> action = ai_system.process_entity(goblin, context)
            >>> if action:
            ...     print(f"{goblin.name} wants to {action.action_type}")
        """
        if not entity.ai_type:
            return None

        ai = self.registry.get(entity.ai_type)
        if not ai:
            return None

        return ai.decide_action(context)

    def process_entities(
        self, entities: List["Entity"], context_factory: Callable[["Entity"], AIContext]
    ) -> List[Tuple["Entity", Optional[AIAction]]]:
        """Process multiple entities and get their AI decisions.

        This is useful for batch processing enemies or NPCs during
        a game turn.

        Args:
            entities: List of entities to process
            context_factory: Function that creates AIContext for each entity

        Returns:
            List of (entity, action) tuples

        Example:
            >>> def make_context(entity):
            ...     return AIContext(
            ...         entity=entity,
            ...         nearby_entities=get_nearby(entity),
            ...         location=world.current_location
            ...     )
            >>>
            >>> results = ai_system.process_entities(enemies, make_context)
            >>> for enemy, action in results:
            ...     if action:
            ...         execute_action(enemy, action)
        """
        results = []
        for entity in entities:
            context = context_factory(entity)
            action = self.process_entity(entity, context)
            results.append((entity, action))
        return results

    def process_entities_with_callback(
        self,
        entities: List["Entity"],
        context_factory: Callable[["Entity"], AIContext],
        action_callback: Callable[["Entity", AIAction], None],
    ) -> int:
        """Process entities and immediately execute their actions via callback.

        This is a convenience method that combines processing and execution.

        Args:
            entities: List of entities to process
            context_factory: Function that creates AIContext for each entity
            action_callback: Function called with (entity, action) for each decision

        Returns:
            Number of entities that took actions

        Example:
            >>> def make_context(entity):
            ...     return AIContext(entity=entity, nearby_entities=get_nearby(entity))
            >>>
            >>> def execute_action(entity, action):
            ...     if action.action_type == "attack":
            ...         combat.attack(entity, action.target)
            ...     elif action.action_type == "move":
            ...         world.move_entity(entity, action.target_position)
            >>>
            >>> count = ai_system.process_entities_with_callback(
            ...     enemies, make_context, execute_action
            ... )
            >>> print(f"{count} enemies took actions")
        """
        count = 0
        for entity, action in self.process_entities(entities, context_factory):
            if action:
                action_callback(entity, action)
                count += 1
        return count

    def has_ai(self, entity: "Entity") -> bool:
        """Check if an entity has AI configured.

        Args:
            entity: Entity to check

        Returns:
            True if entity has an ai_type and it's registered

        Example:
            >>> if ai_system.has_ai(goblin):
            ...     print(f"{goblin.name} has AI")
        """
        return entity.ai_type is not None and self.registry.has(entity.ai_type)
