# Barebones RPG Framework

A flexible, code-first RPG framework for building turn-based games with support for procedural generation and AI-driven content.

## What is this?

Barebones RPG is a Python framework designed to be a foundation for creating RPG games. It provides all the essential systems needed for an RPG (combat, entities, items, quests, dialog, world management, etc.), but with **no content** - making it a perfect starting point for your own games.

The framework is code-first (Python classes and functions), fully extensible (hooks and events throughout), and supports both hand-crafted and procedurally generated content.

## Installation

### Requirements

- Python 3.11+

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd barebones_rpg

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Development Setup

```bash
# Install with dev dependencies
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

## Running the Examples

```bash
# Run the main example
uv run python main.py

# Or run specific examples
uv run python -m barebones_rpg.examples.simple_combat_example
uv run python -m barebones_rpg.examples.mini_rpg
uv run python -m barebones_rpg.examples.tile_based_example
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=barebones_rpg
```

## Documentation

Full documentation is available in the `sphinx_docs/` directory. To build and view:

```bash
./build_docs.sh
# Then open sphinx_docs/_build/html/index.html
```

The documentation includes:
- Getting Started Guide
- Core Concepts and Architecture
- Complete API Reference
- Step-by-Step Tutorials
- In-Depth Guides
- Example Breakdowns

## Quick Example

```python
from barebones_rpg import Game, GameConfig, Character, Enemy, Stats, Combat

# Create game
game = Game(GameConfig(title="My RPG"))

# Create characters
hero = Character(name="Hero", stats=Stats(hp=100, atk=15, defense=5))
goblin = Enemy(name="Goblin", stats=Stats(hp=30, atk=8, defense=2))

# Start combat
combat = Combat(
    player_group=[hero],
    enemy_group=[goblin],
    events=game.events
)
combat.start()
```

See `barebones_rpg/examples/` for complete working examples.

## Project Structure

```
barebones_rpg/
├── core/           # Game engine, events, save/load
├── entities/       # Characters, NPCs, enemies, stats, AI
├── combat/         # Turn-based combat system
├── items/          # Items, inventory, equipment, loot
├── quests/         # Quest and objective tracking
├── dialog/         # Conversation trees
├── world/          # Maps, locations, tiles
├── rendering/      # Pygame renderer
├── loaders/        # Data loaders (JSON/YAML)
└── examples/       # Example games
```

## License

MIT License
