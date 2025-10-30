"""Quest system for managing objectives and storylines.

This module provides a flexible quest system for tracking player progress,
objectives, and rewards.
"""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum, auto
from uuid import uuid4
from pydantic import BaseModel, Field

from ..core.events import EventManager, Event, EventType


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

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique objective ID")
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


class Quest(BaseModel):
    """A quest with objectives and rewards.

    Example:
        >>> quest = Quest(
        ...     name="Save the Village",
        ...     description="The village is under attack by goblins!"
        ... )
        >>> quest.add_objective(QuestObjective(
        ...     description="Defeat goblin chief",
        ...     objective_type=ObjectiveType.KILL_ENEMY,
        ...     target="Goblin Chief"
        ... ))
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique quest ID")
    name: str = Field(description="Quest name")
    description: str = Field(default="", description="Quest description")

    status: QuestStatus = Field(default=QuestStatus.NOT_STARTED, description="Quest status")
    objectives: List[QuestObjective] = Field(
        default_factory=list, description="Quest objectives"
    )

    # Rewards
    exp_reward: int = Field(default=0, description="Experience reward")
    gold_reward: int = Field(default=0, description="Gold reward")
    item_rewards: List[str] = Field(default_factory=list, description="Item rewards (item IDs)")

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

    def add_objective(self, objective: QuestObjective) -> None:
        """Add an objective to the quest.

        Args:
            objective: Objective to add
        """
        self.objectives.append(objective)

    def start(self, events: Optional[EventManager] = None) -> None:
        """Start the quest.

        Args:
            events: Event manager for publishing events
        """
        if self.status == QuestStatus.NOT_STARTED:
            self.status = QuestStatus.ACTIVE

            if self.on_start:
                self.on_start(self)

            if events:
                events.publish(Event(EventType.QUEST_STARTED, {"quest": self}))
                
                # Auto-register event listeners for objectives
                for objective in self.objectives:
                    if objective.objective_type == ObjectiveType.KILL_ENEMY and objective.target:
                        self._register_kill_listener(objective, events)

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
    
    def _register_kill_listener(self, objective: QuestObjective, events: EventManager) -> None:
        """Register event listener for kill objectives.
        
        Args:
            objective: The objective to track
            events: Event manager to subscribe to
        """
        def on_death(event: Event):
            """Handle entity death events."""
            if not self.is_active() or objective.is_completed():
                return
            
            entity = event.data.get('entity')
            if entity and hasattr(entity, 'name') and entity.name == objective.target:
                was_completed = objective.increment(1)
                if was_completed:
                    events.publish(Event(
                        EventType.OBJECTIVE_COMPLETED,
                        {"quest": self, "objective": objective}
                    ))
                    self.check_completion(events)
        
        events.subscribe(EventType.DEATH, on_death)


class QuestManager(BaseModel):
    """Manages all quests in the game.

    Example:
        >>> manager = QuestManager()
        >>> quest = Quest(name="Tutorial Quest")
        >>> manager.add_quest(quest)
        >>> manager.start_quest(quest.id)
    """

    quests: Dict[str, Quest] = Field(default_factory=dict, description="All quests")
    active_quests: List[str] = Field(default_factory=list, description="Active quest IDs")
    completed_quests: List[str] = Field(default_factory=list, description="Completed quest IDs")

    model_config = {"arbitrary_types_allowed": True}

    def add_quest(self, quest: Quest) -> None:
        """Add a quest to the manager.

        Args:
            quest: Quest to add
        """
        self.quests[quest.id] = quest

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

    def complete_quest(self, quest_id: str, events: Optional[EventManager] = None) -> bool:
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
        events: Optional[EventManager] = None
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
                    events.publish(Event(
                        EventType.OBJECTIVE_COMPLETED,
                        {"quest": quest, "objective": objective}
                    ))

        # Check if quest is complete
        if updated:
            quest.check_completion(events)

        return updated

    def save(self) -> Dict[str, Any]:
        """Save quest manager state.

        Returns:
            Dictionary representation
        """
        return {
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            # Individual quests would need to be saved separately
        }

    def load(self, data: Dict[str, Any]) -> None:
        """Load quest manager state.

        Args:
            data: Saved data
        """
        self.active_quests = data.get("active_quests", [])
        self.completed_quests = data.get("completed_quests", [])
