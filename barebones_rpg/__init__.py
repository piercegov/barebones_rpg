"""Barebones RPG Framework.

A flexible, code-first RPG framework for building turn-based games with support
for procedural generation and AI-driven content.
"""

__version__ = "0.1.0"

# Core exports
from .core import Game, GameState, GameConfig, Event, EventType, EventManager

# Entity exports
from .entities import (
    Stats,
    Entity,
    Character,
    NPC,
    Enemy,
    StatusEffect,
    SimplePathfindingAI,
    TacticalAI,
    AIInterface,
    AIContext,
)

# Item exports
from .items import (
    Item,
    ItemType,
    EquipSlot,
    Inventory,
    Equipment,
    create_weapon,
    create_armor,
    create_consumable,
    create_quest_item,
)

# Combat exports
from .combat import (
    Combat,
    CombatState,
    CombatAction,
    ActionResult,
    ActionType,
    AttackAction,
    SkillAction,
    ItemAction,
    RunAction,
    create_attack_action,
    create_skill_action,
    create_heal_skill,
)

# Party exports
from .party import Party

# Dialog exports
from .dialog import DialogNode, DialogChoice, DialogTree, DialogSession, DialogRenderer

# World exports
from .world import Tile, Location, World, TilemapPathfinder, APManager

# Quest exports
from .quests import Quest, QuestObjective, QuestManager, QuestStatus, ObjectiveType

# Rendering exports
from .rendering import (
    Renderer,
    PygameRenderer,
    PygameGameLoop,
    Color,
    Colors,
    UIElement,
    TextBox,
    TileRenderer,
    ClickToMoveHandler,
    TileInteractionHandler,
    UIComponents,
)

__all__ = [
    # Core
    "Game",
    "GameState",
    "GameConfig",
    "Event",
    "EventType",
    "EventManager",
    # Entities
    "Stats",
    "Entity",
    "Character",
    "NPC",
    "Enemy",
    "StatusEffect",
    "SimplePathfindingAI",
    "TacticalAI",
    "AIInterface",
    "AIContext",
    # Items
    "Item",
    "ItemType",
    "EquipSlot",
    "Inventory",
    "Equipment",
    "create_weapon",
    "create_armor",
    "create_consumable",
    "create_quest_item",
    # Combat
    "Combat",
    "CombatState",
    "CombatAction",
    "ActionResult",
    "ActionType",
    "AttackAction",
    "SkillAction",
    "ItemAction",
    "RunAction",
    "create_attack_action",
    "create_skill_action",
    "create_heal_skill",
    # Party
    "Party",
    # Dialog
    "DialogNode",
    "DialogChoice",
    "DialogTree",
    "DialogSession",
    "DialogRenderer",
    # World
    "Tile",
    "Location",
    "World",
    "TilemapPathfinder",
    "APManager",
    # Quests
    "Quest",
    "QuestObjective",
    "QuestManager",
    "QuestStatus",
    "ObjectiveType",
    # Rendering
    "Renderer",
    "PygameRenderer",
    "PygameGameLoop",
    "Color",
    "Colors",
    "UIElement",
    "TextBox",
    "TileRenderer",
    "ClickToMoveHandler",
    "TileInteractionHandler",
    "UIComponents",
]
