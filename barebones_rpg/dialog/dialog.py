"""Dialog system for conversations and choice trees.

This module provides a flexible dialog system for NPC conversations,
branching narratives, and interactive storytelling.
"""

from typing import Optional, List, Dict, Any, Callable
from uuid import uuid4
from pydantic import BaseModel, Field


class DialogConditions:
    """Helper class with common dialog condition factories.

    This provides reusable condition functions for common dialog scenarios,
    reducing boilerplate in dialog tree creation.

    Example:
        >>> from barebones_rpg.quests.quest import QuestStatus
        >>> quest_started = DialogConditions.quest_status(quest, QuestStatus.ACTIVE)
        >>> enemy_dead = DialogConditions.entity_not_in_location(location, "Goblin")
    """

    @staticmethod
    def quest_status(quest, status) -> Callable:
        """Create a condition that checks if a quest has a specific status.

        Args:
            quest: Quest object to check
            status: QuestStatus to check for

        Returns:
            Condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return quest.status == status

        return condition

    @staticmethod
    def quest_not_started(quest) -> Callable:
        """Create a condition that checks if a quest hasn't been started.

        Args:
            quest: Quest object to check

        Returns:
            Condition function
        """
        from ..quests.quest import QuestStatus

        return DialogConditions.quest_status(quest, QuestStatus.NOT_STARTED)

    @staticmethod
    def quest_active(quest) -> Callable:
        """Create a condition that checks if a quest is active.

        Args:
            quest: Quest object to check

        Returns:
            Condition function
        """
        from ..quests.quest import QuestStatus

        return DialogConditions.quest_status(quest, QuestStatus.ACTIVE)

    @staticmethod
    def quest_completed(quest) -> Callable:
        """Create a condition that checks if a quest is completed.

        Args:
            quest: Quest object to check

        Returns:
            Condition function
        """
        from ..quests.quest import QuestStatus

        return DialogConditions.quest_status(quest, QuestStatus.COMPLETED)

    @staticmethod
    def entity_in_location(location, entity_name: str) -> Callable:
        """Create a condition that checks if an entity exists in a location.

        Args:
            location: Location object to check
            entity_name: Name of entity to look for

        Returns:
            Condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return location.has_entity_named(entity_name)

        return condition

    @staticmethod
    def entity_not_in_location(location, entity_name: str) -> Callable:
        """Create a condition that checks if an entity does NOT exist in a location.

        Args:
            location: Location object to check
            entity_name: Name of entity to look for

        Returns:
            Condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return not location.has_entity_named(entity_name)

        return condition

    @staticmethod
    def all_conditions(*conditions: Callable) -> Callable:
        """Create a condition that requires all sub-conditions to be true.

        Args:
            *conditions: Variable number of condition functions

        Returns:
            Combined condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return all(cond(context) for cond in conditions)

        return condition

    @staticmethod
    def any_condition(*conditions: Callable) -> Callable:
        """Create a condition that requires any sub-condition to be true.

        Args:
            *conditions: Variable number of condition functions

        Returns:
            Combined condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return any(cond(context) for cond in conditions)

        return condition

    @staticmethod
    def not_condition(condition_func: Callable) -> Callable:
        """Create a condition that inverts another condition.

        Args:
            condition_func: Condition to invert

        Returns:
            Inverted condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return not condition_func(context)

        return condition

    @staticmethod
    def always() -> Callable:
        """Create a condition that is always true.

        Useful as a fallback or when you want an option always available.

        Returns:
            Always-true condition function
        """

        def condition(context: Dict[str, Any]) -> bool:
            return True

        return condition


class DialogChoice(BaseModel):
    """A choice in a dialog tree.

    Example:
        >>> choice = DialogChoice(
        ...     text="Tell me about the quest",
        ...     next_node_id="quest_info"
        ... )

        >>> # With quest integration
        >>> choice = DialogChoice(
        ...     text="I'll help you!",
        ...     next_node_id="accepted",
        ...     quest_to_start=my_quest
        ... )
    """

    text: str = Field(description="Choice text shown to player")
    next_node_id: Optional[str] = Field(
        default=None, description="ID of next dialog node (None = end dialog)"
    )
    condition: Optional[Callable] = Field(
        default=None, description="Function that returns True if choice is available"
    )
    on_select: Optional[Callable] = Field(
        default=None, description="Function called when choice is selected"
    )

    # Quest integration
    quest_to_start: Optional[Any] = Field(
        default=None, description="Quest object to start when this choice is selected"
    )
    quest_to_update: Optional[tuple] = Field(
        default=None,
        description="Tuple of (quest, objective_type, target, amount) to update when selected",
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def is_available(self, context: Dict[str, Any]) -> bool:
        """Check if this choice is available.

        Args:
            context: Game context for evaluating conditions

        Returns:
            True if choice can be selected
        """
        if self.condition is None:
            return True
        return self.condition(context)

    def select(self, context: Dict[str, Any]) -> Any:
        """Execute the choice's on_select callback and handle quest actions.

        Args:
            context: Game context

        Returns:
            Result of callback (if any)
        """
        # Handle quest starting
        if self.quest_to_start:
            events = context.get("events")
            quest_manager = context.get("quest_manager")
            location = context.get("location")
            world = context.get("world")

            if quest_manager and events:
                quest_manager.start_quest(self.quest_to_start.id, events)
            elif events:
                # Direct start if no manager in context
                # Pass location/world for retroactive progress checking
                self.quest_to_start.start(events, location=location, world=world)

        # Handle quest updating
        if self.quest_to_update:
            from ..quests.quest import ObjectiveType

            quest, objective_type, target, amount = self.quest_to_update
            events = context.get("events")
            quest_manager = context.get("quest_manager")

            if quest_manager and events:
                quest_manager.update_objective(
                    quest.id, objective_type, target, amount, events
                )

        # Execute custom callback
        if self.on_select:
            return self.on_select(context)

        return None


class DialogNode(BaseModel):
    """A node in a dialog tree.

    Each node contains text, optional speaker, and choices for the player.

    Example:
        >>> node = DialogNode(
        ...     id="greeting",
        ...     speaker="Village Elder",
        ...     text="Welcome, traveler. How can I help you?",
        ...     choices=[
        ...         DialogChoice(text="Tell me about the village", next_node_id="village_info"),
        ...         DialogChoice(text="Goodbye", next_node_id=None)
        ...     ]
        ... )
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique node ID")
    speaker: Optional[str] = Field(default=None, description="Speaker name")
    text: str = Field(description="Dialog text")
    choices: List[DialogChoice] = Field(
        default_factory=list, description="Available choices"
    )
    on_enter: Optional[Callable] = Field(
        default=None, description="Function called when node is entered"
    )
    on_exit: Optional[Callable] = Field(
        default=None, description="Function called when node is exited"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def get_available_choices(self, context: Dict[str, Any]) -> List[DialogChoice]:
        """Get all available choices based on current context.

        Args:
            context: Game context for evaluating conditions

        Returns:
            List of available choices
        """
        return [choice for choice in self.choices if choice.is_available(context)]

    def enter(self, context: Dict[str, Any]) -> Any:
        """Call the on_enter callback.

        Args:
            context: Game context

        Returns:
            Result of callback (if any)
        """
        if self.on_enter:
            return self.on_enter(context)
        return None

    def exit(self, context: Dict[str, Any]) -> Any:
        """Call the on_exit callback.

        Args:
            context: Game context

        Returns:
            Result of callback (if any)
        """
        if self.on_exit:
            return self.on_exit(context)
        return None


class DialogTree(BaseModel):
    """A complete dialog tree.

    Contains all nodes and manages navigation through the dialog.

    Example:
        >>> tree = DialogTree(name="Village Elder Dialog")
        >>> tree.add_node(DialogNode(
        ...     id="start",
        ...     speaker="Elder",
        ...     text="Hello!",
        ...     choices=[DialogChoice(text="Hi", next_node_id="greeting")]
        ... ))
        >>> tree.set_start_node("start")
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique tree ID")
    name: str = Field(description="Dialog tree name")
    nodes: Dict[str, DialogNode] = Field(
        default_factory=dict, description="All nodes in the tree"
    )
    start_node_id: Optional[str] = Field(
        default=None, description="ID of starting node"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def add_node(self, node: DialogNode) -> bool:
        """Add a node to the tree.

        Args:
            node: Node to add

        Returns:
            True if node was added successfully
        """
        self.nodes[node.id] = node

        # Auto-set start node if this is the first node
        if self.start_node_id is None:
            self.start_node_id = node.id

        return True

    def get_node(self, node_id: str) -> Optional[DialogNode]:
        """Get a node by ID.

        Args:
            node_id: ID of node to retrieve

        Returns:
            Dialog node or None if not found
        """
        return self.nodes.get(node_id)

    def get_start_node(self) -> Optional[DialogNode]:
        """Get the starting node.

        Returns:
            Start node or None if not set
        """
        if self.start_node_id:
            return self.nodes.get(self.start_node_id)
        return None

    def set_start_node(self, node_id: str) -> bool:
        """Set the starting node.

        Args:
            node_id: ID of the start node

        Returns:
            True if node exists and was set as start node
        """
        if node_id in self.nodes:
            self.start_node_id = node_id
            return True
        return False

    def validate_tree(self) -> List[str]:
        """Validate the dialog tree.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.start_node_id:
            errors.append("No start node set")
        elif self.start_node_id not in self.nodes:
            errors.append(f"Start node '{self.start_node_id}' not found")

        # Check that all referenced nodes exist
        for node in self.nodes.values():
            for choice in node.choices:
                if choice.next_node_id and choice.next_node_id not in self.nodes:
                    errors.append(
                        f"Node '{node.id}' references non-existent node '{choice.next_node_id}'"
                    )

        return errors


class DialogSession:
    """Active dialog session.

    Manages the state of an ongoing conversation. The framework automatically
    populates the context with game systems when a game instance is provided.

    Example:
        >>> tree = DialogTree(name="Test")
        >>> # ... add nodes ...
        >>> # Simple - just pass game, framework handles context
        >>> session = DialogSession(tree, game=game)
        >>> # Or add custom context
        >>> session = DialogSession(tree, game=game, context={"npc_mood": "happy"})
    """

    def __init__(
        self,
        dialog_tree: DialogTree,
        game: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a dialog session.

        Args:
            dialog_tree: The dialog tree to run
            game: Game instance (framework auto-populates context from it)
            context: Additional custom context data
        """
        self.tree = dialog_tree
        self.context = context or {}

        # Auto-populate context from game if provided
        if game:
            self.context["game"] = game
            self.context["quest_manager"] = game.quests
            self.context["events"] = game.events
            # Note: world property not added yet, can be added when needed

        self.current_node_id: Optional[str] = None
        self.history: List[str] = []  # Node IDs visited
        self.is_active = False

    def start(self) -> Optional[DialogNode]:
        """Start the dialog session.

        Returns:
            The starting dialog node
        """
        start_node = self.tree.get_start_node()
        if start_node:
            self.current_node_id = start_node.id
            self.is_active = True
            self.history.append(start_node.id)
            start_node.enter(self.context)
            return start_node
        return None

    def get_current_node(self) -> Optional[DialogNode]:
        """Get the current dialog node.

        Returns:
            Current node or None
        """
        if self.current_node_id:
            return self.tree.get_node(self.current_node_id)
        return None

    def get_available_choices(self) -> List[DialogChoice]:
        """Get available choices at current node.

        Returns:
            List of available choices
        """
        node = self.get_current_node()
        if node:
            return node.get_available_choices(self.context)
        return []

    def make_choice(self, choice_index: int) -> Optional[DialogNode]:
        """Make a choice and navigate to next node.

        Args:
            choice_index: Index of the choice to make

        Returns:
            Next dialog node or None if dialog ended
        """
        if not self.is_active:
            return None

        current = self.get_current_node()
        if not current:
            return None

        choices = self.get_available_choices()
        if choice_index < 0 or choice_index >= len(choices):
            return None

        choice = choices[choice_index]

        # Exit current node
        current.exit(self.context)

        # Execute choice callback
        choice.select(self.context)

        # Navigate to next node
        if choice.next_node_id:
            next_node = self.tree.get_node(choice.next_node_id)
            if next_node:
                self.current_node_id = next_node.id
                self.history.append(next_node.id)
                next_node.enter(self.context)
                return next_node
        else:
            # Dialog ended
            self.end()

        return None

    def end(self) -> None:
        """End the dialog session."""
        if self.current_node_id:
            current = self.get_current_node()
            if current:
                current.exit(self.context)

        self.is_active = False
        self.current_node_id = None


# Helper function for creating simple linear dialogs


def create_linear_dialog(
    name: str, conversations: List[tuple[str, str]], speaker: Optional[str] = None
) -> DialogTree:
    """Create a simple linear dialog (no branching).

    Args:
        name: Dialog name
        conversations: List of (text, speaker) tuples
        speaker: Default speaker name

    Returns:
        Linear dialog tree
    """
    tree = DialogTree(name=name)

    for i, (text, node_speaker) in enumerate(conversations):
        node_id = f"node_{i}"
        next_node_id = f"node_{i+1}" if i < len(conversations) - 1 else None

        node = DialogNode(
            id=node_id,
            speaker=node_speaker or speaker,
            text=text,
            choices=(
                [DialogChoice(text="Continue", next_node_id=next_node_id)]
                if next_node_id
                else []
            ),
        )
        tree.add_node(node)

    return tree
