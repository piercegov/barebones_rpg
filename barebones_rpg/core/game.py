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
    save_directory: str = "saves"

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

        # Save manager
        from .save_manager import SaveManager

        self.save_manager = SaveManager(self.config.save_directory)

        # Registries for serializable objects
        self._entities: Dict[str, Any] = {}
        self._items: Dict[str, Any] = {}
        self._parties: Dict[str, Any] = {}
        self._quests: Dict[str, Any] = {}

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

    def register_entity(self, entity: Any) -> None:
        """Register an entity for saving/loading.

        Args:
            entity: Entity to register
        """
        if hasattr(entity, "id"):
            self._entities[entity.id] = entity

    def register_item(self, item: Any) -> None:
        """Register an item for saving/loading.

        Args:
            item: Item to register
        """
        if hasattr(item, "id"):
            self._items[item.id] = item

    def register_party(self, party: Any) -> None:
        """Register a party for saving/loading.

        Args:
            party: Party to register
        """
        if hasattr(party, "name"):
            self._parties[party.name] = party

    def register_quest(self, quest: Any) -> None:
        """Register a quest for saving/loading.

        Args:
            quest: Quest to register
        """
        if hasattr(quest, "id"):
            self._quests[quest.id] = quest

    def get_entity(self, entity_id: str) -> Any:
        """Get a registered entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self._entities.get(entity_id)

    def get_item(self, item_id: str) -> Any:
        """Get a registered item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item or None if not found
        """
        return self._items.get(item_id)

    def get_party(self, party_name: str) -> Any:
        """Get a registered party by name.

        Args:
            party_name: Party name

        Returns:
            Party or None if not found
        """
        return self._parties.get(party_name)

    def get_quest(self, quest_id: str) -> Any:
        """Get a registered quest by ID.

        Args:
            quest_id: Quest ID

        Returns:
            Quest or None if not found
        """
        return self._quests.get(quest_id)

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

        return QuestManager()

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
        from .serialization import CallbackRegistry

        save_data = {
            "save_name": save_name,
            "clock_time": self.clock_time,
            "state": self.state.name,
            "data": self.data,
            # Save registered entities
            "entities": {
                entity_id: entity.to_dict() if hasattr(entity, "to_dict") else {}
                for entity_id, entity in self._entities.items()
            },
            # Save registered items
            "items": {
                item_id: item.to_dict() if hasattr(item, "to_dict") else {}
                for item_id, item in self._items.items()
            },
            # Save registered parties
            "parties": {
                party_name: party.to_dict() if hasattr(party, "to_dict") else {}
                for party_name, party in self._parties.items()
            },
            # Save registered quests
            "quests": {
                quest_id: quest.to_dict() if hasattr(quest, "to_dict") else {}
                for quest_id, quest in self._quests.items()
            },
            # Systems can implement their own save methods
            "systems": {
                name: system.save() if hasattr(system, "save") else {}
                for name, system in self._systems.items()
            },
            # Save callback registry keys for reference
            "callback_registry": CallbackRegistry.get_all_names(),
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

        # Load entities
        from ..entities.entity import Entity

        entity_data = save_data.get("entities", {})
        self._entities.clear()
        for entity_id, data in entity_data.items():
            try:
                entity = Entity.from_dict(data)
                self._entities[entity_id] = entity
            except Exception as e:
                print(f"Warning: Could not load entity {entity_id}: {e}")

        # Load items
        from ..items.item import Item

        item_data = save_data.get("items", {})
        self._items.clear()
        for item_id, data in item_data.items():
            try:
                item = Item(**data)
                self._items[item_id] = item
            except Exception as e:
                print(f"Warning: Could not load item {item_id}: {e}")

        # Load parties
        from ..party.party import Party

        party_data = save_data.get("parties", {})
        self._parties.clear()
        for party_name, data in party_data.items():
            try:
                party = Party.from_dict(data, self._entities)
                self._parties[party_name] = party
            except Exception as e:
                print(f"Warning: Could not load party {party_name}: {e}")

        # Load quests (handled by QuestManager singleton)
        quest_data = save_data.get("quests", {})
        if quest_data:
            print("Warning: Quest loading not fully implemented yet")

        # Load system states
        system_data = save_data.get("systems", {})
        for name, system in self._systems.items():
            if hasattr(system, "load") and name in system_data:
                system.load(system_data[name])

    def save_to_file(self, save_name: str = "default") -> bool:
        """Save the game to a file.

        Args:
            save_name: Name of the save file

        Returns:
            True if save was successful

        Example:
            >>> game.save_to_file("quicksave")
        """
        save_data = self.save_game(save_name)
        return self.save_manager.save(save_name, save_data)

    def load_from_file(self, save_name: str) -> bool:
        """Load the game from a file.

        Args:
            save_name: Name of the save file to load

        Returns:
            True if load was successful

        Example:
            >>> game.load_from_file("quicksave")
        """
        save_data = self.save_manager.load(save_name)
        if save_data:
            self.load_game(save_data)
            return True
        return False

    def list_saves(self) -> list[str]:
        """List all available save files.

        Returns:
            List of save names
        """
        return self.save_manager.list_saves()

    def delete_save(self, save_name: str) -> bool:
        """Delete a save file.

        Args:
            save_name: Name of the save to delete

        Returns:
            True if deletion was successful
        """
        return self.save_manager.delete(save_name)
