"""Core game engine and state management.

This module provides the main Game class that manages the game loop,
state, and coordinates all systems.
"""

from typing import Optional, Any, Dict, TYPE_CHECKING
from enum import Enum, auto
from dataclasses import dataclass, field

from .events import EventManager, Event, EventType

if TYPE_CHECKING:
    from ..quests.quest import QuestManager


class GameState(Enum):
    """Possible game states."""

    MENU = auto()
    PLAYING = auto()
    COMBAT = auto()
    DIALOG = auto()
    PAUSED = auto()
    GAME_OVER = auto()


@dataclass
class GameConfig:
    """Configuration for the game.

    This can be extended by users to add their own config options.
    """

    title: str = "Barebones RPG"
    screen_width: int = 800
    screen_height: int = 600
    fps: int = 60
    auto_save: bool = True
    debug_mode: bool = False

    # Allow arbitrary additional config
    extra: Dict[str, Any] = field(default_factory=dict)


class Game:
    """Main game engine that manages the game loop and state.

    The Game class is the central hub that coordinates all game systems.
    It manages the game loop, state transitions, and provides access to
    all major systems (entities, world, combat, etc.).

    Example:
        >>> game = Game(GameConfig(title="My RPG"))
        >>> game.events.subscribe(EventType.GAME_START, lambda e: print("Game started!"))
        >>> game.start()
        >>> game.run()  # Start the game loop
    """

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize the game.

        Args:
            config: Game configuration. Uses defaults if not provided.
        """
        self.config = config or GameConfig()
        self.events = EventManager()
        self.state = GameState.MENU
        self.running = False
        self.clock_time = 0.0  # Game time in seconds

        # Systems will be initialized here (combat, world, etc.)
        self._systems: Dict[str, Any] = {}

        # Game data storage (accessible to all systems)
        self.data: Dict[str, Any] = {}

    def register_system(self, name: str, system: Any) -> None:
        """Register a game system (combat, world, etc.).

        Args:
            name: Name of the system (e.g., "combat", "world")
            system: The system instance
        """
        self._systems[name] = system

    def get_system(self, name: str) -> Any:
        """Get a registered system by name.

        Args:
            name: Name of the system

        Returns:
            The system instance or None if not found
        """
        return self._systems.get(name)

    @property
    def quests(self) -> "QuestManager":
        """Access the quest manager singleton.

        Returns:
            The QuestManager singleton instance

        Example:
            >>> game = Game()
            >>> quest = Quest(name="Save the Village")
            >>> game.quests.start_quest(quest.id)
        """
        from ..quests.quest import QuestManager

        return QuestManager.instance()

    def start(self) -> None:
        """Start the game and initialize all systems."""
        self.running = True
        self.state = GameState.PLAYING
        self.events.publish(Event(EventType.GAME_START, {"game": self}))

    def stop(self) -> None:
        """Stop the game."""
        self.running = False
        self.events.publish(Event(EventType.GAME_END, {"game": self}))

    def pause(self) -> None:
        """Pause the game."""
        if self.state != GameState.PAUSED:
            self._previous_state = self.state
            self.state = GameState.PAUSED
            self.events.publish(Event(EventType.GAME_PAUSE, {"game": self}))

    def resume(self) -> None:
        """Resume the game from pause."""
        if self.state == GameState.PAUSED:
            self.state = self._previous_state
            self.events.publish(Event(EventType.GAME_RESUME, {"game": self}))

    def change_state(self, new_state: GameState) -> None:
        """Change the game state.

        Args:
            new_state: The new state to transition to
        """
        old_state = self.state
        self.state = new_state
        self.events.publish(
            Event("state_change", {"old_state": old_state, "new_state": new_state})
        )

    def update(self, delta_time: float) -> None:
        """Update game logic.

        This is called every frame by the game loop.

        Args:
            delta_time: Time elapsed since last frame (in seconds)
        """
        self.clock_time += delta_time

        # Update all registered systems
        for system in self._systems.values():
            if hasattr(system, "update"):
                system.update(delta_time)

    def handle_input(self, input_data: Any) -> None:
        """Handle player input.

        Args:
            input_data: Input data (will be pygame events in the rendering layer)
        """
        # This will be implemented by the rendering layer
        # Systems can subscribe to input events
        pass

    def save_game(self, save_name: str = "default") -> Dict[str, Any]:
        """Save the current game state.

        Args:
            save_name: Name of the save file

        Returns:
            Dictionary containing the game state
        """
        save_data = {
            "save_name": save_name,
            "clock_time": self.clock_time,
            "state": self.state.name,
            "data": self.data,
            # Systems can implement their own save methods
            "systems": {
                name: system.save() if hasattr(system, "save") else {}
                for name, system in self._systems.items()
            },
        }
        return save_data

    def load_game(self, save_data: Dict[str, Any]) -> None:
        """Load a saved game state.

        Args:
            save_data: Dictionary containing the saved game state
        """
        self.clock_time = save_data.get("clock_time", 0.0)
        self.state = GameState[save_data.get("state", "MENU")]
        self.data = save_data.get("data", {})

        # Load system states
        system_data = save_data.get("systems", {})
        for name, system in self._systems.items():
            if hasattr(system, "load") and name in system_data:
                system.load(system_data[name])
