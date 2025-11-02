Barebones RPG Framework Documentation
=====================================

A flexible, code-first Python framework for building turn-based RPG games with support for procedural generation and AI-driven content.

.. image:: https://img.shields.io/badge/python-3.11+-blue.svg
   :alt: Python Version
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :alt: License
   :target: LICENSE

Overview
--------

Barebones RPG is a Python framework designed to be a foundation for creating RPG games. It provides all the essential systems needed for an RPG, but with **no content** - making it a perfect starting point for your own games and stories.

✨ Key Features
~~~~~~~~~~~~~~~

- **Code-First Design**: Primary interface is Python classes and functions for programmatic game creation
- **Fully Extensible**: Hooks, events, and overridable behavior throughout
- **Flexible Architecture**: Supports both hand-crafted and procedurally generated content
- **Turn-Based Combat**: Built-in combat system with extensible action framework
- **Rich Systems**: Entities, items, inventory, quests, dialog trees, world/map management
- **Data Loading**: Optional JSON/YAML support for data-driven content
- **Rendering Abstraction**: Pygame-based UI with clean separation from game logic
- **AI-Ready**: Designed to easily integrate with LLMs for dynamic content generation

🚀 Quick Start
--------------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone <repository-url>
   cd barebones_rpg

   # Install with uv (recommended)
   uv sync --dev

   # Or with pip
   pip install -e ".[dev]"

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg import Game, GameConfig, Character, Enemy, Stats, Combat

   # Create game
   game = Game(GameConfig(title="My RPG"))

   # Create characters
   hero = Character(name="Hero", stats=Stats(hp=100, atk=15, defense=5))
   goblin = Enemy(name="Goblin", stats=Stats(hp=30, atk=8, defense=2))

   # Create combat
   combat = Combat(
       player_group=[hero],
       enemy_group=[goblin],
       events=game.events
   )
   combat.start()

📚 Documentation Sections
-------------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting_started
   core_concepts
   tutorials/index
   guides/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/entities
   api/combat
   api/items
   api/quests
   api/dialog
   api/world
   api/rendering
   api/party

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/simple_combat
   examples/mini_rpg
   examples/tile_based_game
   examples/procedural_generation
   examples/ai_integration

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

