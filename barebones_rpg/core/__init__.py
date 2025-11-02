"""Core game engine and systems."""

from .events import Event, EventType, EventManager
from .game import Game, GameState, GameConfig
from .serialization import CallbackRegistry, SerializationContext
from .save_manager import SaveManager
from .registry import Registry

__all__ = [
    "Event",
    "EventType",
    "EventManager",
    "Game",
    "GameState",
    "GameConfig",
    "CallbackRegistry",
    "SerializationContext",
    "SaveManager",
    "Registry",
]
