"""Event system for the RPG framework.

This module provides a flexible publish-subscribe event system that allows
different parts of the game to communicate without tight coupling.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """Built-in event types. Users can extend this or use custom strings."""

    # Game lifecycle
    GAME_START = auto()
    GAME_END = auto()
    GAME_PAUSE = auto()
    GAME_RESUME = auto()

    # Combat events
    COMBAT_START = auto()
    COMBAT_END = auto()
    COMBAT_TURN_START = auto()
    COMBAT_TURN_END = auto()
    ATTACK = auto()
    DAMAGE_DEALT = auto()
    DAMAGE_TAKEN = auto()
    HEAL = auto()
    DEATH = auto()

    # Entity events
    ENTITY_CREATED = auto()
    ENTITY_DESTROYED = auto()
    STAT_CHANGED = auto()
    LEVEL_UP = auto()

    # Item events
    ITEM_ACQUIRED = auto()
    ITEM_USED = auto()
    ITEM_DROPPED = auto()
    ITEM_EQUIPPED = auto()
    ITEM_UNEQUIPPED = auto()

    # Quest events
    QUEST_STARTED = auto()
    QUEST_COMPLETED = auto()
    QUEST_FAILED = auto()
    OBJECTIVE_COMPLETED = auto()

    # World events
    LOCATION_ENTERED = auto()
    LOCATION_EXITED = auto()
    DOOR_OPENED = auto()
    CHEST_OPENED = auto()

    # Dialog events
    DIALOG_STARTED = auto()
    DIALOG_ENDED = auto()
    CHOICE_MADE = auto()


@dataclass
class Event:
    """Base event class that carries event data."""

    event_type: EventType | str
    data: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class EventManager:
    """Central event manager for publish-subscribe pattern.

    This allows different parts of the game to communicate without tight coupling.
    Components can subscribe to events and publish events without knowing about
    each other.

    Example:
        >>> events = EventManager()
        >>> def on_damage(event):
        ...     print(f"Damage dealt: {event.data['amount']}")
        >>> events.subscribe(EventType.DAMAGE_DEALT, on_damage)
        >>> events.publish(Event(EventType.DAMAGE_DEALT, {"amount": 10}))
        Damage dealt: 10
    """

    def __init__(self):
        self._subscribers: Dict[EventType | str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._record_history = False

    def subscribe(
        self, event_type: EventType | str, callback: Callable[[Event], None]
    ) -> None:
        """Subscribe a callback function to an event type.

        Args:
            event_type: The type of event to listen for
            callback: Function to call when event is published. Takes Event as argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(
        self, event_type: EventType | str, callback: Callable[[Event], None]
    ) -> None:
        """Unsubscribe a callback from an event type.

        Args:
            event_type: The type of event to stop listening for
            callback: The callback function to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish
        """
        if self._record_history:
            self._event_history.append(event)

        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                callback(event)

    def enable_history(self) -> None:
        """Enable recording of all published events."""
        self._record_history = True

    def disable_history(self) -> None:
        """Disable recording of events."""
        self._record_history = False

    def get_history(self) -> List[Event]:
        """Get the history of all published events."""
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()

    def clear_all_subscribers(self) -> None:
        """Remove all event subscribers. Useful for cleanup."""
        self._subscribers.clear()
