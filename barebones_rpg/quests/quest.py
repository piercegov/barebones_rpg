"""Quest system for managing objectives and storylines.

This module provides a flexible quest system for tracking player progress,
objectives, and rewards.
"""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum, auto
from uuid import uuid4
from pydantic import BaseModel, Field

from ..core.events import EventManager, Event, EventType
from ..core.singleton import Singleton


class QuestStatus(Enum):
    """Quest status states."""

    NOT_STARTED = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    FAILED = auto()


class ObjectiveType(Enum):
    """Types of quest objectives."""

    KILL_ENEMY = auto()
    COLLECT_ITEM = auto()
    TALK_TO_NPC = auto()
    REACH_LOCATION = auto()
    CUSTOM = auto()


class QuestObjective(BaseModel):
    """A single objective within a quest.

    Example:
        >>> objective = QuestObjective(
        ...     description="Defeat 5 goblins",
        ...     objective_type=ObjectiveType.KILL_ENEMY,
        ...     target="Goblin",
        ...     target_count=5
        ... )
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique objective ID"
    )
    description: str = Field(description="Objective description")
    objective_type: ObjectiveType = Field(description="Type of objective")

    # Progress tracking
    current_count: int = Field(default=0, description="Current progress")
    target_count: int = Field(default=1, description="Required progress")
    completed: bool = Field(default=False, description="Is objective completed")

    # Target (enemy name, item name, NPC name, location name, etc.)
    target: Optional[str] = Field(default=None, description="Target identifier")

    # Custom condition for completion
    condition: Optional[Callable] = Field(
        default=None, description="Custom function to check completion"
    )

    # Callbacks
    on_progress: Optional[Callable] = Field(
        default=None, description="Function called when progress is made"
    )
    on_complete: Optional[Callable] = Field(
        default=None, description="Function called when objective is completed"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def increment(self, amount: int = 1) -> bool:
        """Increment progress on this objective.

        Args:
            amount: Amount to increment by

        Returns:
            True if objective was just completed
        """
        if self.completed:
            return False

        self.current_count += amount

        if self.on_progress:
            self.on_progress(self)

        if self.current_count >= self.target_count:
            self.complete()
            return True

        return False

    def complete(self) -> None:
        """Mark objective as completed."""
        if not self.completed:
            self.completed = True
            if self.on_complete:
                self.on_complete(self)

    def is_completed(self) -> bool:
        """Check if objective is completed.

        Returns:
            True if completed
        """
        if self.completed:
            return True

        if self.condition:
            return self.condition(self)

        return self.current_count >= self.target_count

    def get_progress_text(self) -> str:
        """Get progress text for this objective.

        Returns:
            Progress string like "3/5"
        """
        return f"{self.current_count}/{self.target_count}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert objective to dictionary for saving.

        Returns:
            Dictionary representation
        """
        from ..core.serialization import serialize_callback, encode_enum

        data = self.model_dump(exclude={"condition", "on_progress", "on_complete"})

        # Serialize callbacks
        if self.condition:
            callback_key = serialize_callback(self.condition)
            if callback_key:
                data["condition_callback"] = callback_key

        if self.on_progress:
            callback_key = serialize_callback(self.on_progress)
            if callback_key:
                data["on_progress_callback"] = callback_key

        if self.on_complete:
            callback_key = serialize_callback(self.on_complete)
            if callback_key:
                data["on_complete_callback"] = callback_key

        # Encode enums
        if "objective_type" in data:
            data["objective_type"] = encode_enum(data["objective_type"])

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestObjective":
        """Create objective from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            QuestObjective instance
        """
        from ..core.serialization import deserialize_callback, decode_enum

        # Make a copy to avoid modifying original
        data = data.copy()

        # Decode enum
        if "objective_type" in data and isinstance(data["objective_type"], str):
            data["objective_type"] = decode_enum(ObjectiveType, data["objective_type"])

        # Deserialize callbacks
        condition_key = data.pop("condition_callback", None)
        if condition_key:
            data["condition"] = deserialize_callback(condition_key)

        on_progress_key = data.pop("on_progress_callback", None)
        if on_progress_key:
            data["on_progress"] = deserialize_callback(on_progress_key)

        on_complete_key = data.pop("on_complete_callback", None)
        if on_complete_key:
            data["on_complete"] = deserialize_callback(on_complete_key)

        return cls(**data)


class Quest(BaseModel):
    """A quest with objectives and rewards.

    Quests automatically register themselves with the QuestManager singleton
    when created.

    Example:
        >>> quest = Quest(
        ...     name="Save the Village",
        ...     description="The village is under attack by goblins!"
        ... )  # Automatically registers to QuestManager
        >>> quest.add_objective(QuestObjective(
        ...     description="Defeat goblin chief",
        ...     objective_type=ObjectiveType.KILL_ENEMY,
        ...     target="Goblin Chief"
        ... ))
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique quest ID")
    name: str = Field(description="Quest name")
    description: str = Field(default="", description="Quest description")

    status: QuestStatus = Field(
        default=QuestStatus.NOT_STARTED, description="Quest status"
    )
    objectives: List[QuestObjective] = Field(
        default_factory=list, description="Quest objectives"
    )

    # Rewards
    exp_reward: int = Field(default=0, description="Experience reward")
    gold_reward: int = Field(default=0, description="Gold reward")
    item_rewards: List[str] = Field(
        default_factory=list, description="Item rewards (item IDs)"
    )

    # Quest giver
    giver_npc_id: Optional[str] = Field(default=None, description="NPC who gave quest")

    # Requirements
    required_level: int = Field(default=1, description="Required level to start")
    required_quests: List[str] = Field(
        default_factory=list, description="Quest IDs that must be completed first"
    )

    # Callbacks
    on_start: Optional[Callable] = Field(
        default=None, description="Function called when quest starts"
    )
    on_complete: Optional[Callable] = Field(
        default=None, description="Function called when quest is completed"
    )
    on_fail: Optional[Callable] = Field(
        default=None, description="Function called when quest fails"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data):
        """Initialize quest.

        Note: Quests are not automatically registered to QuestManager.
        Call QuestManager().add_quest(quest) explicitly if you want to use
        the quest manager.
        """
        super().__init__(**data)

    def add_objective(self, objective: QuestObjective) -> bool:
        """Add an objective to the quest.

        Args:
            objective: Objective to add

        Returns:
            True if objective was added successfully
        """
        self.objectives.append(objective)
        return True

    def start(
        self,
        events: Optional[EventManager] = None,
        location: Optional[Any] = None,
        world: Optional[Any] = None,
    ) -> None:
        """Start the quest.

        Args:
            events: Event manager for publishing events
            location: Optional location to check for retroactive progress (e.g., checking if entities still exist)
            world: Optional world to check for retroactive progress across all locations
        """
        if self.status == QuestStatus.NOT_STARTED:
            self.status = QuestStatus.ACTIVE

            if self.on_start:
                self.on_start(self)

            if events:
                events.publish(Event(EventType.QUEST_STARTED, {"quest": self}))

                # Auto-register event listeners for objectives
                for objective in self.objectives:
                    if (
                        objective.objective_type == ObjectiveType.KILL_ENEMY
                        and objective.target
                    ):
                        self._register_kill_listener(objective, events)

                # Check for retroactive progress (e.g., if unique enemies are already dead)
                self.check_retroactive_progress(events, location, world)

    def complete(self, events: Optional[EventManager] = None) -> None:
        """Complete the quest.

        Args:
            events: Event manager for publishing events
        """
        if self.status == QuestStatus.ACTIVE:
            self.status = QuestStatus.COMPLETED

            if self.on_complete:
                self.on_complete(self)

            if events:
                events.publish(Event(EventType.QUEST_COMPLETED, {"quest": self}))

    def fail(self, events: Optional[EventManager] = None) -> None:
        """Fail the quest.

        Args:
            events: Event manager for publishing events
        """
        if self.status == QuestStatus.ACTIVE:
            self.status = QuestStatus.FAILED

            if self.on_fail:
                self.on_fail(self)

            if events:
                events.publish(Event(EventType.QUEST_FAILED, {"quest": self}))

    def check_completion(self, events: Optional[EventManager] = None) -> bool:
        """Check if all objectives are completed.

        Args:
            events: Event manager for publishing events

        Returns:
            True if quest should be completed
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        all_completed = all(obj.is_completed() for obj in self.objectives)
        if all_completed:
            self.complete(events)
            return True

        return False

    def is_active(self) -> bool:
        """Check if quest is active.

        Returns:
            True if quest is active
        """
        return self.status == QuestStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if quest is completed.

        Returns:
            True if quest is completed
        """
        return self.status == QuestStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if quest is failed.

        Returns:
            True if quest is failed
        """
        return self.status == QuestStatus.FAILED

    def get_progress_percentage(self) -> float:
        """Get overall progress percentage.

        Returns:
            Progress from 0.0 to 1.0
        """
        if not self.objectives:
            return 1.0

        completed = sum(1 for obj in self.objectives if obj.is_completed())
        return completed / len(self.objectives)

    def check_retroactive_progress(
        self,
        events: Optional[EventManager] = None,
        location: Optional[Any] = None,
        world: Optional[Any] = None,
    ) -> None:
        """Check for retroactive progress on objectives.

        This method checks if objectives can be completed based on current world state,
        even if the required actions happened before the quest was started.

        For example, if a quest requires killing a unique enemy (tracked by ID) and that
        enemy is already dead when the quest starts, this will mark the objective complete.

        Objectives with ID-based targets (UUIDs) are considered unique and will be checked
        retroactively. Name-based targets are considered generic and won't be checked.

        Args:
            events: Event manager for publishing events
            location: Location to check for entity existence (for single-location quests)
            world: World to check for entity existence (for multi-location quests)
        """
        if not self.is_active():
            return

        for objective in self.objectives:
            if objective.is_completed():
                continue

            # Only check KILL_ENEMY objectives with ID-based targets
            if (
                objective.objective_type == ObjectiveType.KILL_ENEMY
                and objective.target
            ):
                # Check if target looks like a UUID (ID-based) vs a name (generic)
                is_uuid = self._is_uuid_format(objective.target)

                if is_uuid:
                    # This is a unique target - check if it still exists
                    entity_exists = False

                    if location:
                        # Check in specific location
                        entity_exists = any(
                            hasattr(e, "id") and e.id == objective.target
                            for e in location.entities
                        )
                    elif world:
                        # Check in all locations of the world
                        for loc in world.locations.values():
                            entity_exists = any(
                                hasattr(e, "id") and e.id == objective.target
                                for e in loc.entities
                            )
                            if entity_exists:
                                break

                    # If entity doesn't exist, it was already killed - mark objective complete
                    if not entity_exists:
                        was_completed = objective.increment(
                            objective.target_count - objective.current_count
                        )
                        if was_completed and events:
                            events.publish(
                                Event(
                                    EventType.OBJECTIVE_COMPLETED,
                                    {"quest": self, "objective": objective},
                                )
                            )

        # Check if quest is now complete
        if events:
            self.check_completion(events)

    def _is_uuid_format(self, value: str | None) -> bool:
        """Check if a string looks like a UUID.

        Args:
            value: String to check

        Returns:
            True if string appears to be a UUID
        """
        if value is None:
            return False

        # UUIDs are 36 characters with hyphens in specific positions
        # Example: "550e8400-e29b-41d4-a716-446655440000"
        if len(value) != 36:
            return False

        parts = value.split("-")
        if len(parts) != 5:
            return False

        # Check part lengths: 8-4-4-4-12
        expected_lengths = [8, 4, 4, 4, 12]
        if [len(p) for p in parts] != expected_lengths:
            return False

        # Check if all parts are hexadecimal
        try:
            for part in parts:
                int(part, 16)
            return True
        except ValueError:
            return False

    def _register_kill_listener(
        self, objective: QuestObjective, events: EventManager
    ) -> None:
        """Register event listener for kill objectives.

        This method handles both name-based (generic) and ID-based (unique) targets:
        - Name-based: Matches any entity with the target name (e.g., "Goblin")
        - ID-based: Matches only the specific entity with the target ID (UUID)

        Args:
            objective: The objective to track
            events: Event manager to subscribe to
        """
        # Determine if target is ID-based or name-based
        is_uuid = self._is_uuid_format(objective.target)

        def on_death(event: Event):
            """Handle entity death events."""
            if not self.is_active() or objective.is_completed():
                return

            if not event.data:
                return

            entity = event.data.get("entity")
            if not entity:
                return

            # Match based on target type
            matches = False
            if is_uuid:
                # ID-based: match by entity ID
                matches = hasattr(entity, "id") and entity.id == objective.target
            else:
                # Name-based: match by entity name
                matches = hasattr(entity, "name") and entity.name == objective.target

            if matches:
                was_completed = objective.increment(1)
                if was_completed:
                    events.publish(
                        Event(
                            EventType.OBJECTIVE_COMPLETED,
                            {"quest": self, "objective": objective},
                        )
                    )
                    self.check_completion(events)

        events.subscribe(EventType.DEATH, on_death)

    def to_dict(self) -> Dict[str, Any]:
        """Convert quest to dictionary for saving.

        Returns:
            Dictionary representation
        """
        from ..core.serialization import serialize_callback, encode_enum

        data = self.model_dump(
            exclude={"on_start", "on_complete", "on_fail", "objectives"}
        )

        # Serialize callbacks
        if self.on_start:
            callback_key = serialize_callback(self.on_start)
            if callback_key:
                data["on_start_callback"] = callback_key

        if self.on_complete:
            callback_key = serialize_callback(self.on_complete)
            if callback_key:
                data["on_complete_callback"] = callback_key

        if self.on_fail:
            callback_key = serialize_callback(self.on_fail)
            if callback_key:
                data["on_fail_callback"] = callback_key

        # Serialize objectives
        data["objectives"] = [obj.to_dict() for obj in self.objectives]

        # Encode enum
        if "status" in data:
            data["status"] = encode_enum(data["status"])

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], auto_register: bool = False) -> "Quest":
        """Create quest from dictionary.

        Args:
            data: Dictionary representation
            auto_register: If True, register to QuestManager (default: False to avoid duplicates)

        Returns:
            Quest instance
        """
        from ..core.serialization import deserialize_callback, decode_enum

        # Make a copy to avoid modifying original
        data = data.copy()

        # Decode enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = decode_enum(QuestStatus, data["status"])

        # Deserialize callbacks
        on_start_key = data.pop("on_start_callback", None)
        if on_start_key:
            data["on_start"] = deserialize_callback(on_start_key)

        on_complete_key = data.pop("on_complete_callback", None)
        if on_complete_key:
            data["on_complete"] = deserialize_callback(on_complete_key)

        on_fail_key = data.pop("on_fail_callback", None)
        if on_fail_key:
            data["on_fail"] = deserialize_callback(on_fail_key)

        # Deserialize objectives
        objectives_data = data.pop("objectives", [])
        objectives = [
            QuestObjective.from_dict(obj_data) for obj_data in objectives_data
        ]
        data["objectives"] = objectives

        # Create quest without auto-registering if requested
        if not auto_register:
            # Temporarily bypass auto-registration
            quest = object.__new__(cls)
            BaseModel.__init__(quest, **data)
            return quest
        else:
            return cls(**data)


class QuestManager(metaclass=Singleton):
    """Manages all quests in the game (Singleton).

    This is a framework-managed singleton. Access by instantiating directly: QuestManager()

    Example:
        >>> quest = Quest(name="Tutorial Quest")  # Auto-registers
        >>> QuestManager().start_quest(quest.id)
        >>> # Or via game instance:
        >>> game.quests.start_quest(quest.id)
    """

    def __init__(self):
        """Initialize the quest manager."""
        self.quests: Dict[str, Quest] = {}
        self.active_quests: List[str] = []
        self.completed_quests: List[str] = []

    @classmethod
    def reset(cls) -> None:
        """Reset manager to initial state (for testing).

        Clears the singleton instance, causing the next access to create
        a fresh instance with default initialization.
        """
        if cls in Singleton._instances:
            del Singleton._instances[cls]

    def add_quest(self, quest: Quest) -> bool:
        """Add a quest to the manager.

        Automatically registers any callbacks (on_start, on_complete, on_fail) to
        the CallbackRegistry for serialization support.

        Args:
            quest: Quest to add

        Returns:
            True if quest was added successfully
        """
        from ..core.serialization import CallbackRegistry

        # Auto-register quest callbacks
        if quest.on_start:
            CallbackRegistry.register(f"quest.{quest.id}.on_start", quest.on_start)
        if quest.on_complete:
            CallbackRegistry.register(
                f"quest.{quest.id}.on_complete", quest.on_complete
            )
        if quest.on_fail:
            CallbackRegistry.register(f"quest.{quest.id}.on_fail", quest.on_fail)

        # Auto-register objective callbacks
        for i, objective in enumerate(quest.objectives):
            if objective.condition:
                CallbackRegistry.register(
                    f"quest.{quest.id}.objective.{i}.condition", objective.condition
                )
            if objective.on_progress:
                CallbackRegistry.register(
                    f"quest.{quest.id}.objective.{i}.on_progress", objective.on_progress
                )
            if objective.on_complete:
                CallbackRegistry.register(
                    f"quest.{quest.id}.objective.{i}.on_complete", objective.on_complete
                )

        self.quests[quest.id] = quest
        return True

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID.

        Args:
            quest_id: Quest ID

        Returns:
            Quest or None
        """
        return self.quests.get(quest_id)

    def get_quest_by_name(self, name: str) -> Optional[Quest]:
        """Get a quest by name.

        Args:
            name: Quest name

        Returns:
            Quest or None
        """
        for quest in self.quests.values():
            if quest.name == name:
                return quest
        return None

    def start_quest(self, quest_id: str, events: Optional[EventManager] = None) -> bool:
        """Start a quest.

        Args:
            quest_id: Quest ID to start
            events: Event manager

        Returns:
            True if quest was started
        """
        quest = self.get_quest(quest_id)
        if quest and quest.status == QuestStatus.NOT_STARTED:
            quest.start(events)
            if quest.id not in self.active_quests:
                self.active_quests.append(quest.id)
            return True
        return False

    def complete_quest(
        self, quest_id: str, events: Optional[EventManager] = None
    ) -> bool:
        """Complete a quest.

        Args:
            quest_id: Quest ID
            events: Event manager

        Returns:
            True if quest was completed
        """
        quest = self.get_quest(quest_id)
        if quest and quest.is_active():
            quest.complete(events)
            if quest.id in self.active_quests:
                self.active_quests.remove(quest.id)
            if quest.id not in self.completed_quests:
                self.completed_quests.append(quest.id)
            return True
        return False

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests.

        Returns:
            List of active quests
        """
        return [self.quests[qid] for qid in self.active_quests if qid in self.quests]

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests.

        Returns:
            List of completed quests
        """
        return [self.quests[qid] for qid in self.completed_quests if qid in self.quests]

    def update_objective(
        self,
        quest_id: str,
        objective_type: ObjectiveType,
        target: str,
        amount: int = 1,
        events: Optional[EventManager] = None,
    ) -> bool:
        """Update progress on matching objectives.

        This is a helper method for common objective updates like killing enemies
        or collecting items.

        Args:
            quest_id: Quest ID
            objective_type: Type of objective
            target: Target identifier
            amount: Amount to increment
            events: Event manager

        Returns:
            True if any objectives were updated
        """
        quest = self.get_quest(quest_id)
        if not quest or not quest.is_active():
            return False

        updated = False
        for objective in quest.objectives:
            if (
                objective.objective_type == objective_type
                and objective.target == target
                and not objective.is_completed()
            ):
                was_completed = objective.increment(amount)
                updated = True

                if was_completed and events:
                    events.publish(
                        Event(
                            EventType.OBJECTIVE_COMPLETED,
                            {"quest": quest, "objective": objective},
                        )
                    )

        # Check if quest is complete
        if updated:
            quest.check_completion(events)

        return updated

    def save(self) -> Dict[str, Any]:
        """Save quest manager state.

        Returns:
            Dictionary representation including quest state
        """
        return {
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            # Individual quests would need to be saved separately
        }

    def load(self, data: Dict[str, Any]) -> None:
        """Load quest manager state.

        Args:
            data: Saved data containing quest tracking
        """
        self.active_quests = data.get("active_quests", [])
        self.completed_quests = data.get("completed_quests", [])
