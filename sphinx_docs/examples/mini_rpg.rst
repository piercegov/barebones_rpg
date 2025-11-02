Mini RPG Example
================

A complete mini RPG demonstrating multiple systems working together.

Overview
--------

This example demonstrates:

- World with multiple locations
- NPCs with dialog trees
- Quest system
- Combat encounters
- Item management
- Save/load functionality

The mini RPG includes:

- A starting village with NPCs
- A shopkeeper for buying items
- A quest giver
- A dungeon with enemies
- Boss battle

Running the Example
-------------------

.. code-block:: bash

   # Run the mini RPG
   uv run python -m barebones_rpg.examples.mini_rpg

   # Or directly
   python -m barebones_rpg.examples.mini_rpg

Game Features
-------------

Exploration
~~~~~~~~~~~

Move through different locations:

- **Village**: Safe zone with NPCs and shops
- **Forest**: Medium difficulty area
- **Dungeon**: High difficulty with boss

Dialog System
~~~~~~~~~~~~~

Talk to NPCs:

- Shopkeeper for buying/selling items
- Quest giver for accepting quests
- Townspeople for lore and hints

Combat System
~~~~~~~~~~~~~

Engage in turn-based battles:

- Choose actions: Attack, Use Item, Run
- Manage HP and MP
- Defeat enemies for EXP and loot

Quest Progression
~~~~~~~~~~~~~~~~~

Complete objectives:

- Accept quests from NPCs
- Track progress
- Earn rewards

Code Structure
--------------

The example is organized into:

.. code-block:: python

   # Setup
   def setup_game():
       """Initialize game, world, and systems."""
       pass

   # Content creation
   def create_hero():
       """Create the player character."""
       pass

   def create_npcs():
       """Create NPCs with dialog."""
       pass

   def create_enemies():
       """Create enemies for combat."""
       pass

   def create_quests():
       """Set up quest system."""
       pass

   # Main loop
   def main():
       """Run the game loop."""
       setup_game()
       while running:
           handle_input()
           update_game()
           render()

Key Implementation Details
---------------------------

World Setup
~~~~~~~~~~~

.. code-block:: python

   world = World(name="Game World")
   
   village = Location(name="Village", width=20, height=20)
   dungeon = Location(name="Dungeon", width=30, height=30)
   
   world.add_location(village)
   world.add_location(dungeon)
   world.connect_locations(village.id, "north", dungeon.id)

NPC Dialog
~~~~~~~~~~

.. code-block:: python

   dialog_tree = DialogTree(name="Shopkeeper")
   
   greeting = DialogNode(
       id="greeting",
       speaker="Shopkeeper",
       text="Welcome! What can I get you?",
       choices=[
           DialogChoice(text="Buy items", next_node_id="shop"),
           DialogChoice(text="Goodbye", next_node_id=None)
       ]
   )
   
   dialog_tree.add_node(greeting)
   
   shopkeeper = NPC(
       name="Shopkeeper",
       dialog_tree=dialog_tree
   )

Quest System
~~~~~~~~~~~~

.. code-block:: python

   quest = Quest(
       name="Clear the Dungeon",
       description="Defeat the dungeon boss",
       exp_reward=500,
       gold_reward=200
   )
   
   quest.add_objective(QuestObjective(
       description="Defeat Boss",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Dungeon Boss",
       target_count=1
   ))

Combat Integration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def start_combat(hero, enemies):
       combat = Combat(
           player_group=[hero],
           enemy_group=enemies,
           events=game.events
       )
       
       combat.on_victory(handle_victory)
       combat.on_defeat(handle_defeat)
       combat.start()
       
       return combat

Learning Points
---------------

1. **System Integration**: See how different systems work together
2. **Event-Driven Design**: Events coordinate between systems
3. **State Management**: Game state transitions (exploration, combat, dialog)
4. **Content Organization**: Structure your game content effectively

Next Steps
----------

- Study the full source code in ``barebones_rpg/examples/mini_rpg.py``
- Try the :doc:`tile_based_game` for grid-based gameplay
- Learn about :doc:`procedural_generation` for dynamic content
- Read the :doc:`../tutorials/index` for detailed guides

