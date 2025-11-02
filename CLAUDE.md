# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Barebones RPG Framework is a flexible, code-first Python framework for building turn-based RPG games with support for procedural generation and AI-driven content. It provides core systems (entities, combat, items, quests, dialog, world) but no game content—making it a foundation for creating custom RPGs.

## Development Commands

### Dependency Management
```bash
# Install dependencies (uses uv)
uv sync

# Install with dev dependencies
uv sync --dev

# Alternative with pip
pip install -e ".[dev]"
```

### Running the Application
```bash
# Run the main example (mini RPG)
uv run python main.py

# Run specific examples
uv run python -m barebones_rpg.examples.simple_combat_example
uv run python -m barebones_rpg.examples.mini_rpg
uv run python -m barebones_rpg.examples.tile_based_example
```

### Testing
```bash
# Run tests with pytest
uv run pytest

# Run specific test file
uv run pytest tests/test_combat.py
```

### Code Quality
```bash
# Format code with black
uv run black .

# Type checking with mypy
uv run mypy barebones_rpg
```

## Architecture

### Core Design Pattern
The framework uses an **event-driven architecture** with a central `EventManager` that enables loose coupling between systems. The `Game` class acts as the central hub coordinating all systems through an event pub-sub pattern.

### System Organization
- **core/**: Event system (`EventManager`) and game engine (`Game`, `GameState`, `GameConfig`), generic `Registry` base class
- **entities/**: Entity base classes (`Entity`, `Character`, `NPC`, `Enemy`) with stats and leveling systems, AI interface (`AIInterface`, `AIContext`, `AIAction`, `AIRegistry`, `AISystem`)
- **combat/**: Turn-based combat system with action framework (`Combat`, `CombatAction`, `AttackAction`)
- **items/**: Item system with inventory, equipment, and loot drops (`Item`, `Inventory`, `Equipment`, `LootRegistry`, `LootDrop`)
- **quests/**: Quest tracking with objectives (`Quest`, `QuestObjective`, `QuestManager`)
- **dialog/**: Conversation trees with choices (`DialogTree`, `DialogNode`, `DialogSession`)
- **world/**: World/map management (`World`, `Location`, `Tile`)
- **rendering/**: Abstract renderer with Pygame implementation (swappable)
- **loaders/**: Data loaders for JSON/YAML content
- **examples/**: Complete example games demonstrating framework usage

### Key Architectural Patterns

**Event-Driven Communication**: Systems communicate via events rather than direct references. For example, when an entity levels up, it publishes a `LEVEL_UP` event that other systems can subscribe to.

**System Registration**: The `Game` class maintains a registry of systems (combat, world, etc.) that can be accessed by name. Systems can implement `update()`, `save()`, and `load()` methods that the game engine calls automatically.

**Code-First Design**: The primary API is Python code, not data files. Items, entities, quests, and dialogs can be created programmatically, making it ideal for procedural generation and AI-driven content.

**Extensibility Through Inheritance**: All core classes (`Entity`, `Item`, `CombatAction`, etc.) are designed to be extended. Custom behavior is added through inheritance or callbacks rather than modifying framework code.

## Important Implementation Notes

### Event System
All major systems rely on the event system. When implementing features:
- Subscribe to relevant events in `EventType` enum (defined in core/events.py)
- Publish events when significant actions occur
- Pass the `EventManager` instance to methods that trigger events (e.g., `entity.gain_exp(100, game.events)`)

### Entity Stats
Entities use a `StatsManager` that supports temporary stat modifiers via `StatusEffect`. Always use `stats_manager.get_effective_stat()` rather than accessing raw stat values directly.

### Combat Flow
Combat is turn-based with these phases:
1. Combat start → `COMBAT_START` event
2. Turn order determined by speed stat
3. For each turn: `COMBAT_TURN_START` → action execution → `COMBAT_TURN_END`
4. Combat ends → `COMBAT_END` event with victory/defeat data

### Rendering Abstraction
Game logic is completely separate from rendering. The `Renderer` abstract class defines the interface. Pygame is the default implementation, but any renderer can be swapped in without modifying game code.

### Loot System
The loot system supports hybrid data-driven and code-first approaches:
- **LootRegistry**: Global registry for mapping item names to templates or factory functions
- **Hybrid Support**: Loot tables can reference items by string name (registry lookup) or use Item objects directly
- **Automatic Drops**: Combat system automatically rolls loot tables when enemies die and publishes `ITEM_DROPPED` events
- **Unique Items**: Items with `unique=True` only drop once per game (tracked by LootRegistry)
- **Manual Collection**: Framework handles drop generation, but users must subscribe to events or call `combat.get_dropped_loot()` to add items to player inventory

Enemy loot table format: `[{"item": "Name" or Item, "chance": 0.0-1.0, "quantity": N}]`

### AI System
The framework provides a flexible AI interface system for entity behavior:
- **AIInterface**: Abstract base class that all AI implementations must inherit from
- **AIContext**: Context object passed to AI containing entity state, nearby entities, location, etc.
- **AIAction**: Action object returned by AI describing what the entity wants to do
- **AIRegistry**: Global registry for sharing AI instances across multiple entities (memory efficient)
- **AISystem**: Helper system for executing AI and building contexts

Users implement custom AI by inheriting from `AIInterface` and implementing `decide_action(context)`. The AI system supports any approach: state machines, behavior trees, utility AI, LLM-based decisions, or any custom logic.

Example:
```python
class AggressiveMeleeAI(AIInterface):
    def decide_action(self, context: AIContext) -> Optional[AIAction]:
        if context.nearby_entities:
            target = context.nearby_entities[0]
            distance = abs(context.entity.position[0] - target.position[0]) + abs(context.entity.position[1] - target.position[1])
            if distance <= 1:
                return AIAction(action_type="attack", target=target)
            return AIAction(action_type="move", target_position=target.position)
        return AIAction(action_type="wait")

# Register once, use for many entities
AIRegistry.register("aggressive_melee", AggressiveMeleeAI())
goblin1 = Enemy(name="Goblin 1", ai_type="aggressive_melee")
goblin2 = Enemy(name="Goblin 2", ai_type="aggressive_melee")  # Shares same AI instance
```

## Project Requirements

- Python 3.11+
- pygame >= 2.5.0
- pydantic >= 2.0.0
- pyyaml >= 6.0

## Save/Load System

The framework includes a comprehensive save/load system with callback serialization support.

### Key Components
- **SaveManager**: Handles JSON file I/O, directory management, and versioning
- **CallbackRegistry**: Manages serialization of callback functions by symbolic names
- **Game Registration**: Entities, items, parties, and quests can be registered for automatic serialization

### Basic Usage
```python
from barebones_rpg.core import Game, GameConfig, CallbackRegistry

# 1. Register callbacks before creating items/quests
def heal_50(entity, context):
    entity.heal(50)

CallbackRegistry.register("heal_50", heal_50)

# 2. Configure save directory
config = GameConfig(save_directory="saves")
game = Game(config)

# 3. Register game objects
hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
game.register_entity(hero)

# 4. Save and load
game.save_to_file("my_save")
game.load_from_file("my_save")
```

### Callback Serialization
Callbacks in items, quests, and other systems are automatically serialized by name:
- Register callbacks with `CallbackRegistry.register(name, callback)` before creating objects
- Callbacks are stored as symbolic names in save files
- On load, callbacks are restored from the registry
- Unregistered callbacks trigger auto-registration with a warning

### Extending Save System
Custom systems can implement `save()` and `load()` methods:
```python
class MySystem:
    def save(self) -> Dict[str, Any]:
        return {"my_data": self.data}
    
    def load(self, data: Dict[str, Any]) -> None:
        self.data = data.get("my_data")

# Register with game
game.register_system("my_system", my_system)
# Automatically saved/loaded with game state
```

## Development Patterns

### Creating Custom Content
Prefer programmatic creation over data files. Example:
```python
# Good: Programmatic creation enables procedural generation
def generate_enemy(level):
    return Enemy(
        name=f"Level {level} Goblin",
        stats=Stats(hp=50 + level * 10, atk=5 + level * 2)
    )

# Also valid: Data-driven for static content
enemies = EntityLoader.load_enemies("data/enemies.json")
```

### Extending Systems
Always extend through inheritance or composition, never modify framework files:
```python
# Custom combat action
class CounterAction(CombatAction):
    def execute(self, source, target, context):
        # Custom implementation
        pass
```

### Testing Integration
When testing systems, always mock or provide the `EventManager` since most systems require it for proper operation.
