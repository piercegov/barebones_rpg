Simple Combat Example
=====================

A basic combat example demonstrating the core combat system.

Overview
--------

This example shows how to:

- Create a hero and enemy
- Set up a combat encounter
- Execute basic attacks
- Handle combat victory/defeat

Full Example
------------

.. code-block:: python

   from barebones_rpg import (
       Game, GameConfig, Character, Enemy, Stats,
       Combat, AttackAction
   )

   # Initialize game
   config = GameConfig(title="Simple Combat Example")
   game = Game(config)

   # Create hero
   hero = Character(
       name="Hero",
       stats=Stats(
           hp=100, max_hp=100,
           mp=20, max_mp=20,
           atk=15, defense=5,
           speed=10
       )
   )

   # Create enemy
   slime = Enemy(
       name="Slime",
       stats=Stats(
           hp=30, max_hp=30,
           atk=5, defense=1,
           speed=6
       ),
       exp_reward=25,
       gold_reward=10
   )

   # Create combat
   combat = Combat(
       player_group=[hero],
       enemy_group=[slime],
       events=game.events
   )

   # Set up callbacks
   def on_victory(combat_state):
       print("\\nVictory!")
       print(f"Gained {slime.exp_reward} EXP")
       hero.gain_exp(slime.exp_reward, game.events)

   def on_defeat(combat_state):
       print("\\nDefeat! Game Over.")

   combat.on_victory(on_victory)
   combat.on_defeat(on_defeat)

   # Start combat
   combat.start()
   print("Combat started!")

   # Combat loop
   turn = 1
   while not combat.is_finished():
       print(f"\\n--- Turn {turn} ---")
       current = combat.get_current_turn_entity()
       print(f"{current.name}'s turn")

       if current == hero:
           # Player attacks
           action = AttackAction()
           result = combat.execute_action(action, hero, slime)
           print(f"Hero attacks Slime for {result.data.get('damage', 0)} damage!")
       else:
           # Enemy attacks
           action = AttackAction()
           result = combat.execute_action(action, slime, hero)
           print(f"Slime attacks Hero for {result.data.get('damage', 0)} damage!")

       # Display HP
       print(f"Hero HP: {hero.stats.hp}/{hero.stats.max_hp}")
       print(f"Slime HP: {slime.stats.hp}/{slime.stats.max_hp}")

       combat.next_turn()
       turn += 1

   print("\\nCombat ended!")

Key Concepts
------------

Combat Initialization
~~~~~~~~~~~~~~~~~~~~~

The ``Combat`` class requires:

- ``player_group``: List of player-controlled entities
- ``enemy_group``: List of enemy entities
- ``events``: EventManager for publishing combat events

Turn Management
~~~~~~~~~~~~~~~

The combat system automatically:

- Determines turn order based on speed stats
- Tracks whose turn it is
- Handles turn transitions

Action Execution
~~~~~~~~~~~~~~~~

Actions are executed with:

.. code-block:: python

   result = combat.execute_action(action, source, target)

The result contains:

- ``success``: Whether the action succeeded
- ``message``: Description of what happened
- ``data``: Additional information (damage dealt, etc.)

Next Steps
----------

- Try the :doc:`mini_rpg` for a more complete example
- Learn about :doc:`tile_based_game` for grid-based combat
- Read the :doc:`../api/combat` documentation

