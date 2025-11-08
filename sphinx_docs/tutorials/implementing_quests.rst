Implementing Quests
===================

This tutorial will guide you through creating and managing quests in your RPG. You'll learn how to create quests, track objectives, integrate with events, handle rewards, and build quest chains.

Overview
--------

The Barebones RPG Framework provides a comprehensive quest system with:

- **Quest Management**: Automatic registration and tracking
- **Flexible Objectives**: Kill enemies, collect items, talk to NPCs, reach locations, or custom conditions
- **Event Integration**: Automatic progress tracking through game events
- **Rewards**: Experience, gold, and item rewards
- **Quest Chains**: Prerequisites and level requirements
- **Callbacks**: Custom logic for quest lifecycle events

What You'll Build
~~~~~~~~~~~~~~~~~

In this tutorial, you'll create:

1. A basic quest with a single objective
2. A multi-objective quest with event integration
3. A quest chain with prerequisites
4. Custom objectives with callbacks

Basic Quest Creation
--------------------

Let's start with a simple quest:

.. code-block:: python

   from barebones_rpg import Quest, QuestObjective, ObjectiveType, QuestManager

   # Create a quest
   quest = Quest(
       name="Goblin Trouble",
       description="The goblins are threatening the village!",
       exp_reward=100,
       gold_reward=50
   )

   # Add an objective
   quest.add_objective(QuestObjective(
       description="Defeat 5 goblins",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin",
       target_count=5
   ))

   # Access the quest manager and add the quest
   quest_manager = QuestManager()
   quest_manager.add_quest(quest)

   # Start the quest
   quest_manager.start_quest(quest.id, events=game.events)

Key Points
~~~~~~~~~~

- **Explicit Registration**: Quests must be explicitly added to ``QuestManager`` with ``add_quest()``
- **Quest IDs**: Each quest gets a unique ID generated automatically
- **Rewards**: Set ``exp_reward``, ``gold_reward``, and ``item_rewards`` when creating the quest
- **Optional Manager**: You can manage quests yourself without using ``QuestManager`` if desired

Quest Objectives
----------------

Objectives define what the player needs to accomplish. The framework supports several objective types:

Objective Types
~~~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg import QuestObjective, ObjectiveType

   # Kill enemy objective
   kill_objective = QuestObjective(
       description="Defeat the Goblin Chief",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin Chief",
       target_count=1
   )

   # Collect item objective
   collect_objective = QuestObjective(
       description="Collect 3 healing herbs",
       objective_type=ObjectiveType.COLLECT_ITEM,
       target="Healing Herb",
       target_count=3
   )

   # Talk to NPC objective
   talk_objective = QuestObjective(
       description="Speak with the village elder",
       objective_type=ObjectiveType.TALK_TO_NPC,
       target="Elder Marcus"
   )

   # Reach location objective
   location_objective = QuestObjective(
       description="Travel to the Dark Forest",
       objective_type=ObjectiveType.REACH_LOCATION,
       target="Dark Forest"
   )

   # Custom objective (with custom logic)
   custom_objective = QuestObjective(
       description="Reach level 10",
       objective_type=ObjectiveType.CUSTOM,
       condition=lambda obj: hero.level >= 10
   )

Progress Tracking
~~~~~~~~~~~~~~~~~

Each objective tracks its progress with ``current_count`` and ``target_count``:

.. code-block:: python

   objective = QuestObjective(
       description="Defeat 5 goblins",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin",
       target_count=5
   )

   # Check progress
   print(objective.get_progress_text())  # "0/5"

   # Manually increment progress
   objective.increment(1)
   print(objective.get_progress_text())  # "1/5"

   # Check if completed
   if objective.is_completed():
       print("Objective complete!")

Event Integration
-----------------

The quest system automatically tracks progress through the event system, making quest implementation seamless.

Automatic Kill Tracking
~~~~~~~~~~~~~~~~~~~~~~~~

When you start a quest with ``KILL_ENEMY`` objectives, the quest system automatically subscribes to death events:

.. code-block:: python

   from barebones_rpg import (
       Quest, QuestObjective, ObjectiveType,
       Game, GameConfig, Character, Enemy, Combat, Stats
   )

   # Initialize game
   game = Game(GameConfig(title="Quest Example"))

   # Create hero
   hero = Character(
       name="Hero",
       stats=Stats(strength=15, constitution=12, dexterity=10,
                   intelligence=8, charisma=10, base_max_hp=50,
                   hp=100, mp=50)
   )
   hero.init_inventory()

   # Create quest with kill objective
   quest = Quest(
       name="Goblin Slayer",
       description="Defeat 3 goblins",
       exp_reward=150
   )
   quest.add_objective(QuestObjective(
       description="Defeat 3 goblins",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin",
       target_count=3
   ))

   # Start the quest (registers kill listener automatically)
   quest.start(events=game.events)

   # Create and defeat goblins
   for i in range(3):
       goblin = Enemy(
           name="Goblin",
           stats=Stats(strength=8, constitution=6, dexterity=12,
                      intelligence=5, charisma=5, base_max_hp=20, hp=30),
           exp_reward=50
       )
       
       # Combat automatically publishes death events
       combat = Combat(
           player_group=[hero],
           enemy_group=[goblin],
           events=game.events
       )
       combat.start()
       # ... execute combat ...

   # Quest automatically tracks kills and completes when done
   if quest.is_completed():
       print(f"Quest complete! Gained {quest.exp_reward} EXP")

Manual Objective Updates
~~~~~~~~~~~~~~~~~~~~~~~~~

For other objective types, update progress manually:

.. code-block:: python

   # Using QuestManager helper method
   quest_manager = QuestManager()
   
   # When player collects an item
   quest_manager.update_objective(
       quest_id=quest.id,
       objective_type=ObjectiveType.COLLECT_ITEM,
       target="Healing Herb",
       amount=1,
       events=game.events
   )

   # When player talks to NPC
   quest_manager.update_objective(
       quest_id=quest.id,
       objective_type=ObjectiveType.TALK_TO_NPC,
       target="Elder Marcus",
       events=game.events
   )

   # Or update objectives directly
   for objective in quest.objectives:
       if objective.objective_type == ObjectiveType.REACH_LOCATION:
           if hero.current_location == objective.target:
               objective.complete()
               quest.check_completion(events=game.events)

Quest Rewards
-------------

Quests can provide experience, gold, and items as rewards:

.. code-block:: python

   quest = Quest(
       name="Village Defender",
       description="Protect the village from goblins",
       exp_reward=200,
       gold_reward=100,
       item_rewards=["potion_healing", "sword_iron"]
   )

Handling Rewards
~~~~~~~~~~~~~~~~

Listen for quest completion events to distribute rewards:

.. code-block:: python

   from barebones_rpg import EventType, Event

   def on_quest_complete(event: Event):
       quest = event.data.get("quest")
       if quest:
           # Award experience
           hero.gain_exp(quest.exp_reward, game.events)
           
           # Award gold
           hero.inventory.add_gold(quest.gold_reward)
           
           # Award items
           for item_id in quest.item_rewards:
               item = create_item_from_id(item_id)
               hero.inventory.add_item(item)
           
           print(f"Quest '{quest.name}' completed!")
           print(f"Rewards: {quest.exp_reward} EXP, {quest.gold_reward} gold")

   # Subscribe to quest completion events
   game.events.subscribe(EventType.QUEST_COMPLETED, on_quest_complete)

Quest Chains and Prerequisites
-------------------------------

Create quest chains by setting prerequisites:

Level Requirements
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   quest = Quest(
       name="Advanced Mission",
       description="A quest for experienced adventurers",
       required_level=10,
       exp_reward=500
   )

   # Check if player can start quest
   if hero.stats.level >= quest.required_level:
       quest_manager.start_quest(quest.id, events=game.events)
   else:
       print(f"You must be level {quest.required_level} to start this quest")

Quest Prerequisites
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # First quest in chain
   quest1 = Quest(
       name="The Beginning",
       description="Start your adventure",
       exp_reward=100
   )
   quest1.add_objective(QuestObjective(
       description="Defeat 5 slimes",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Slime",
       target_count=5
   ))

   # Second quest requires first to be complete
   quest2 = Quest(
       name="The Continuation",
       description="Your journey continues",
       required_quests=[quest1.id],
       exp_reward=200
   )
   quest2.add_objective(QuestObjective(
       description="Defeat the Goblin King",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin King"
   ))

   # Third quest requires second to be complete
   quest3 = Quest(
       name="The Finale",
       description="The final challenge",
       required_quests=[quest2.id],
       required_level=15,
       exp_reward=500
   )

   # Check prerequisites before starting
   def can_start_quest(quest, hero, quest_manager):
       # Check level
       if hero.stats.level < quest.required_level:
           return False
       
       # Check required quests
       completed_ids = [q.id for q in quest_manager.get_completed_quests()]
       for req_id in quest.required_quests:
           if req_id not in completed_ids:
               return False
       
       return True

Custom Objectives and Callbacks
--------------------------------

Add custom logic with callbacks for advanced quest behavior.

Custom Conditions
~~~~~~~~~~~~~~~~~

Use custom conditions for unique objective requirements:

.. code-block:: python

   # Objective with custom completion condition
   objective = QuestObjective(
       description="Have at least 1000 gold",
       objective_type=ObjectiveType.CUSTOM,
       condition=lambda obj: hero.inventory.gold >= 1000
   )

   # Check condition
   if objective.is_completed():
       print("Objective complete!")

Quest Callbacks
~~~~~~~~~~~~~~~

Add callbacks for quest lifecycle events:

.. code-block:: python

   def on_quest_start(quest):
       print(f"Quest started: {quest.name}")
       print(quest.description)
       # Spawn enemies, unlock areas, etc.

   def on_quest_complete(quest):
       print(f"Quest completed: {quest.name}")
       # Unlock new quests, open gates, etc.

   def on_quest_fail(quest):
       print(f"Quest failed: {quest.name}")
       # Handle failure consequences

   quest = Quest(
       name="Special Mission",
       description="A quest with callbacks",
       on_start=on_quest_start,
       on_complete=on_quest_complete,
       on_fail=on_quest_fail,
       exp_reward=300
   )

Objective Callbacks
~~~~~~~~~~~~~~~~~~~

Track progress with objective-level callbacks:

.. code-block:: python

   def on_objective_progress(objective):
       print(f"Progress: {objective.get_progress_text()}")

   def on_objective_complete(objective):
       print(f"Objective completed: {objective.description}")

   objective = QuestObjective(
       description="Defeat 10 goblins",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin",
       target_count=10,
       on_progress=on_objective_progress,
       on_complete=on_objective_complete
   )

Complete Example
----------------

Here's a full example integrating all concepts:

.. code-block:: python

   from barebones_rpg import (
       Game, GameConfig, Character, Enemy, Stats, Combat,
       Quest, QuestObjective, ObjectiveType, QuestManager,
       EventType, Event, AttackAction
   )

   # Initialize game
   config = GameConfig(title="Quest System Demo")
   game = Game(config)

   # Create hero
   hero = Character(
       name="Brave Knight",
       character_class="warrior",
       stats=Stats(
           strength=15, constitution=12, dexterity=10,
           intelligence=8, charisma=10, base_max_hp=50,
           hp=100, mp=50
       )
   )
   hero.init_inventory()

   # Create a multi-objective quest
   def on_quest_start(quest):
       print(f"\n{'='*50}")
       print(f"QUEST STARTED: {quest.name}")
       print(f"{'='*50}")
       print(quest.description)
       print("\nObjectives:")
       for i, obj in enumerate(quest.objectives, 1):
           print(f"  {i}. {obj.description}")

   def on_quest_complete(quest):
       print(f"\n{'='*50}")
       print(f"QUEST COMPLETED: {quest.name}")
       print(f"{'='*50}")
       print(f"Rewards:")
       print(f"  - {quest.exp_reward} EXP")
       print(f"  - {quest.gold_reward} Gold")

   quest = Quest(
       name="Goblin Threat",
       description="The village is under attack by goblins!",
       exp_reward=300,
       gold_reward=150,
       on_start=on_quest_start,
       on_complete=on_quest_complete
   )

   # Add multiple objectives
   quest.add_objective(QuestObjective(
       description="Defeat 3 Goblin Warriors",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin Warrior",
       target_count=3,
       on_progress=lambda obj: print(f"  → {obj.description}: {obj.get_progress_text()}")
   ))

   quest.add_objective(QuestObjective(
       description="Defeat the Goblin Chief",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin Chief",
       target_count=1,
       on_complete=lambda obj: print(f"  ✓ {obj.description} - COMPLETE!")
   ))

   # Start quest
   quest.start(events=game.events)

   # Create and fight enemies
   print("\n--- Combat Phase ---\n")
   
   # Fight goblin warriors
   for i in range(3):
       print(f"Encounter {i+1}: Goblin Warrior")
       warrior = Enemy(
           name="Goblin Warrior",
           stats=Stats(
               strength=10, constitution=8, dexterity=12,
               intelligence=5, charisma=5, base_max_hp=30, hp=40
           ),
           exp_reward=50
       )
       
       combat = Combat(
           player_group=[hero],
           enemy_group=[warrior],
           events=game.events
       )
       combat.start()
       
       # Simple combat loop
       while combat.is_active():
           current = combat.get_current_combatant()
           if current == hero:
               action = AttackAction()
               combat.execute_action(action, hero, [warrior])
               combat.end_turn()
       
       print(f"Defeated Goblin Warrior {i+1}\n")

   # Fight the chief
   print("Final Encounter: Goblin Chief")
   chief = Enemy(
       name="Goblin Chief",
       stats=Stats(
           strength=15, constitution=12, dexterity=10,
           intelligence=8, charisma=8, base_max_hp=50, hp=80
       ),
       exp_reward=100
   )
   
   combat = Combat(
       player_group=[hero],
       enemy_group=[chief],
       events=game.events
   )
   combat.start()
   
   while combat.is_active():
       current = combat.get_current_combatant()
       if current == hero:
           action = AttackAction()
           combat.execute_action(action, hero, [chief])
           combat.end_turn()

   print("Defeated Goblin Chief!\n")

   # Check quest completion
   quest.check_completion(events=game.events)

   # Access quest manager
   quest_manager = QuestManager()
   print(f"\nActive quests: {len(quest_manager.get_active_quests())}")
   print(f"Completed quests: {len(quest_manager.get_completed_quests())}")

Best Practices
--------------

Quest Organization
~~~~~~~~~~~~~~~~~~

1. **Use Descriptive Names**: Make quest and objective descriptions clear and specific
2. **Balance Objectives**: Mix different objective types for variety
3. **Appropriate Rewards**: Scale rewards to quest difficulty

Progress Tracking
~~~~~~~~~~~~~~~~~

1. **Leverage Events**: Use automatic event tracking for kill objectives
2. **Manual Updates**: Call ``update_objective()`` for custom tracking
3. **Check Completion**: Always call ``check_completion()`` after manual updates

Quest Chains
~~~~~~~~~~~~

1. **Logical Progression**: Ensure prerequisites make narrative sense
2. **Level Gating**: Use ``required_level`` to prevent players from accessing difficult content too early
3. **Clear Requirements**: Communicate prerequisites to players

Performance
~~~~~~~~~~~

1. **Event Cleanup**: Quest listeners are automatically managed
2. **Quest Manager**: Use the singleton to avoid creating multiple managers
3. **Save/Load**: Quest state is automatically serialized with the game

Common Patterns
~~~~~~~~~~~~~~~

**Story Progression Quest**:

.. code-block:: python

   quest = Quest(
       name="The Hero's Journey",
       required_quests=[previous_quest.id],
       required_level=5
   )
   quest.add_objective(QuestObjective(
       description="Talk to the village elder",
       objective_type=ObjectiveType.TALK_TO_NPC,
       target="Elder"
   ))

**Fetch Quest**:

.. code-block:: python

   quest = Quest(name="Herb Gathering")
   quest.add_objective(QuestObjective(
       description="Collect 5 healing herbs",
       objective_type=ObjectiveType.COLLECT_ITEM,
       target="Healing Herb",
       target_count=5
   ))

**Kill Quest**:

.. code-block:: python

   quest = Quest(name="Monster Slayer")
   quest.add_objective(QuestObjective(
       description="Defeat 10 slimes",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Slime",
       target_count=10
   ))

**Boss Quest**:

.. code-block:: python

   quest = Quest(
       name="Dragon's Lair",
       required_level=20,
       exp_reward=1000
   )
   quest.add_objective(QuestObjective(
       description="Defeat the ancient dragon",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Ancient Dragon",
       target_count=1
   ))

Next Steps
----------

Now that you understand the quest system:

1. Try creating a quest chain for your game's storyline
2. Experiment with custom objectives using conditions
3. Integrate quests with the :doc:`creating_dialog_trees` system
4. Review the :doc:`../api/quests` for complete API documentation
5. Check out the :doc:`../examples/mini_rpg` for a complete implementation

