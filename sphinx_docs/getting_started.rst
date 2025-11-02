Getting Started
===============

This guide will help you get up and running with Barebones RPG Framework.

Installation
------------

Requirements
~~~~~~~~~~~~

- Python 3.11 or higher
- pygame >= 2.5.0
- pydantic >= 2.0.0
- pyyaml >= 6.0

Using uv (Recommended)
~~~~~~~~~~~~~~~~~~~~~~

`uv <https://github.com/astral-sh/uv>`_ provides fast, reliable dependency management:

.. code-block:: bash

   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Clone the repository
   git clone https://github.com/PierceGov/barebones_rpg.git
   cd barebones_rpg

   # Install dependencies
   uv sync

   # Or with dev dependencies
   uv sync --dev

Using pip
~~~~~~~~~

.. code-block:: bash

   pip install -e .
   # Or with dev dependencies
   pip install -e ".[dev]"

Running Examples
----------------

The framework includes several example games to help you understand how to use it:

.. code-block:: bash

   # Run the mini RPG example
   uv run python main.py

   # Run specific examples
   uv run python -m barebones_rpg.examples.simple_combat_example
   uv run python -m barebones_rpg.examples.mini_rpg
   uv run python -m barebones_rpg.examples.tile_based_example

Your First Game
---------------

Let's create a simple combat encounter:

.. code-block:: python

   from barebones_rpg import (
       Game, GameConfig, Character, Enemy, Stats,
       Combat, AttackAction
   )

   # Initialize the game
   config = GameConfig(title="My First RPG")
   game = Game(config)

   # Create a hero
   hero = Character(
       name="Brave Knight",
       character_class="warrior",
       stats=Stats(
           strength=15,
           constitution=12,
           dexterity=10,
           intelligence=8,
           charisma=10,
           base_max_hp=50,
           base_max_mp=20,
           hp=100,
           mp=50
       )
   )

   # Create an enemy
   goblin = Enemy(
       name="Goblin",
       stats=Stats(
           strength=8,
           constitution=6,
           dexterity=12,
           intelligence=5,
           charisma=5,
           base_max_hp=20,
           hp=30
       ),
       exp_reward=50,
       gold_reward=10
   )

   # Create and start combat
   combat = Combat(
       player_group=[hero],
       enemy_group=[goblin],
       events=game.events
   )
   
   # Set up victory callback
   def on_victory(combat_state):
       print("Victory! You defeated the goblin!")
       hero.gain_exp(goblin.exp_reward, game.events)
   
   combat.on_victory(on_victory)
   combat.start()

   # Execute combat actions
   while combat.is_active():
       current_entity = combat.get_current_combatant()
       
       if current_entity == hero:
           # Player's turn
           action = AttackAction()
           combat.execute_action(action, hero, [goblin])
           combat.end_turn()
       # Enemy turns are handled automatically by the combat system

Next Steps
----------

Now that you have the framework installed and running:

1. Read the :doc:`core_concepts` guide to understand the architecture
2. Explore the :doc:`tutorials/index` for in-depth walkthroughs
3. Check out the :doc:`api/core` for detailed API documentation
4. Study the example games in ``barebones_rpg/examples/``

Common Issues
-------------

Import Errors
~~~~~~~~~~~~~

If you get import errors, make sure you've installed the package:

.. code-block:: bash

   uv sync
   # or
   pip install -e .

Pygame Initialization Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If pygame fails to initialize, ensure you have the required system libraries installed:

- **Linux**: ``sudo apt-get install python3-pygame``
- **macOS**: pygame should work out of the box
- **Windows**: pygame should work after pip installation

Getting Help
------------

- Check the :doc:`tutorials/index` for detailed guides
- Read through the example games
- Review the API documentation for specific systems

