Core Concepts
=============

This guide introduces the fundamental concepts and architecture of the Barebones RPG Framework.

Architecture Overview
---------------------

Event-Driven Design
~~~~~~~~~~~~~~~~~~~

The framework uses an **event-driven architecture** with a central ``EventManager`` that enables loose coupling between systems. The ``Game`` class acts as the central hub coordinating all systems through an event pub-sub pattern.

.. code-block:: python

   from barebones_rpg import EventType, Game

   game = Game()

   # Subscribe to events
   def on_level_up(event):
       entity = event.data['entity']
       print(f"{entity.name} reached level {entity.level}!")

   game.events.subscribe(EventType.LEVEL_UP, on_level_up)

   # Systems publish events automatically
   hero.gain_exp(100, game.events)  # Triggers LEVEL_UP event

System Organization
~~~~~~~~~~~~~~~~~~~

The framework is organized into modular systems:

- **core/**: Event system, game engine, state management, save/load
- **entities/**: Entity base classes, stats, leveling, AI interface
- **combat/**: Turn-based combat with extensible actions
- **items/**: Items, inventory, equipment, loot drops
- **quests/**: Quest tracking with objectives
- **dialog/**: Conversation trees with choices
- **world/**: World/map management with locations and tiles
- **rendering/**: Abstract renderer with Pygame implementation
- **party/**: Party management for multiple characters

The Game Loop
-------------

Game States
~~~~~~~~~~~

The ``Game`` class manages different game states:

.. code-block:: python

   from barebones_rpg import Game, GameConfig, GameState

   config = GameConfig(
       title="My RPG",
       screen_width=800,
       screen_height=600,
       fps=60
   )

   game = Game(config)
   
   # Change states
   game.change_state(GameState.PLAYING)
   game.change_state(GameState.COMBAT)
   game.change_state(GameState.DIALOG)

System Registration
~~~~~~~~~~~~~~~~~~~

Custom systems can be registered with the game engine:

.. code-block:: python

   class MyCustomSystem:
       def update(self, delta_time):
           """Called every frame."""
           pass
       
       def save(self):
           """Return data to be saved."""
           return {"my_data": self.data}
       
       def load(self, data):
           """Load saved data."""
           self.data = data.get("my_data")

   game.register_system("my_system", MyCustomSystem())

Entities and Characters
-----------------------

The Entity Hierarchy
~~~~~~~~~~~~~~~~~~~~

All game objects that have stats and can perform actions inherit from ``Entity``:

- ``Entity``: Base class for all living/interactive objects
- ``Character``: Player-controlled characters
- ``NPC``: Non-player characters for dialog and quests
- ``Enemy``: Hostile entities for combat

.. code-block:: python

   from barebones_rpg import Character, NPC, Enemy, Stats

   # Player character
   hero = Character(
       name="Hero",
       character_class="warrior",
       level=1,
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

   # Friendly NPC
   merchant = NPC(
       name="Shopkeeper",
       dialog_tree=merchant_dialog
   )

   # Enemy
   dragon = Enemy(
       name="Ancient Dragon",
       stats=Stats(
           strength=50,
           constitution=40,
           dexterity=15,
           intelligence=30,
           charisma=20,
           base_max_hp=400,
           hp=500
       ),
       exp_reward=1000,
       gold_reward=500,
       loot_table=[
           {"item": "Dragon Scale", "chance": 0.5},
           {"item": "Dragon Tooth", "chance": 0.3}
       ]
   )

Stats System
~~~~~~~~~~~~

Entities use a ``StatsManager`` that supports temporary modifiers:

.. code-block:: python

   from barebones_rpg import StatusEffect

   # Add a temporary buff
   hero.stats_manager.add_status_effect(
       StatusEffect(
           name="Strength Potion",
           duration=5,  # 5 turns
           stat_modifiers={"atk": 10, "defense": 5}
       )
   )

   # Always use effective stats (includes modifiers)
   effective_attack = hero.stats_manager.get_effective_stat("atk")

Combat System
-------------

Turn-Based Combat
~~~~~~~~~~~~~~~~~

The combat system manages turn order, action execution, and combat flow:

.. code-block:: python

   from barebones_rpg import Combat, AttackAction, create_skill_action

   combat = Combat(
       player_group=[hero, mage],
       enemy_group=[goblin1, goblin2, goblin3],
       events=game.events
   )

   # Set up callbacks
   combat.on_victory(lambda c: print("Victory!"))
   combat.on_defeat(lambda c: print("Game Over!"))
   
   combat.start()

Combat Actions
~~~~~~~~~~~~~~

The framework includes built-in actions and supports custom actions:

- ``AttackAction``: Basic physical attack
- ``SkillAction``: Magic/special abilities with MP costs
- ``ItemAction``: Use consumable items
- ``RunAction``: Attempt to flee from combat

.. code-block:: python

   # Built-in actions
   attack = AttackAction()
   combat.execute_action(attack, hero, [goblin])

   # Custom skill
   fireball = create_skill_action(
       name="Fireball",
       mp_cost=15,
       damage_multiplier=2.0,
       damage_type="magic",
       max_targets=1
   )
   combat.execute_action(fireball, mage, [goblin])

Items and Inventory
-------------------

Item System
~~~~~~~~~~~

Items come in different types with various properties:

.. code-block:: python

   from barebones_rpg import (
       create_weapon, create_armor, create_consumable,
       EquipSlot, ItemType
   )

   # Equipment
   sword = create_weapon("Excalibur", base_damage=25, value=1000)
   armor = create_armor("Plate Mail", physical_defense=15, 
                       slot=EquipSlot.BODY, value=800)

   # Consumables with callbacks
   def heal_effect(entity, context):
       entity.heal(50)
       print(f"{entity.name} recovered 50 HP!")

   potion = create_consumable(
       "Health Potion",
       on_use=heal_effect,
       stackable=True,
       max_stack=99,
       value=25
   )

.. note::
   **Best Practice**: For items with callbacks (like consumables with ``on_use``), 
   register them with ``LootManager`` to enable automatic callback serialization 
   for save/load. See the Loot System section below.

Inventory Management
~~~~~~~~~~~~~~~~~~~~

Entities can have inventory and equipment systems:

.. code-block:: python

   from barebones_rpg.items import LootManager

   # Initialize inventory and equipment
   hero.init_inventory(max_slots=20)
   hero.init_equipment()

   # Add items to inventory
   # For items without callbacks, create directly
   hero.inventory.add_item(sword)
   
   # For items with callbacks, get from LootManager (if registered)
   potion = LootManager().get("health_potion")
   if potion:
       hero.inventory.add_item(potion)

   # Equip items
   old_weapon = hero.equipment.equip(sword)
   
   # Get stat bonuses from equipment
   total_atk_bonus = hero.equipment.get_total_stat_bonus("atk")

Loot System
~~~~~~~~~~~

The ``LootManager`` is the **recommended way** to manage items, especially those with 
callbacks. It provides:

- **Automatic callback registration** for save/load serialization
- **Template-based item creation** (instances are created when needed)
- **String-based references** in loot tables
- **Unique item tracking** to prevent duplicate drops

.. code-block:: python

   from barebones_rpg.items import LootManager, create_consumable, create_weapon

   # Define callback
   def heal_effect(entity, context):
       entity.heal(50)
       return 50

   # Create item templates
   health_potion = create_consumable(
       "Health Potion",
       on_use=heal_effect,  # Callback will be auto-registered!
       stackable=True,
       value=50
   )
   
   rare_sword = create_weapon("Legendary Blade", base_damage=25, value=1000)
   
   # Register with LootManager (callbacks auto-registered for serialization)
   LootManager().register("health_potion", health_potion)
   LootManager().register("rare_sword", rare_sword)
   
   # Get item instances when needed
   potion = LootManager().get("health_potion")
   hero.inventory.add_item(potion)
   
   # Use in loot tables
   boss = Enemy(
       name="Boss",
       stats=Stats(hp=200, max_hp=200, atk=25, defense=20),
       loot_table=[
           {"item": "health_potion", "chance": 0.3},
           {"item": "rare_sword", "chance": 0.05}
       ]
   )

   # Handle loot via events
   def on_loot_drop(event):
       loot = event.data.get("loot_drop")
       player.inventory.add_item(loot.item)

   game.events.subscribe(EventType.ITEM_DROPPED, on_loot_drop)

Quests and Objectives
----------------------

Quest System
~~~~~~~~~~~~

Track player progress with quests and objectives:

.. code-block:: python

   from barebones_rpg import (
       Quest, QuestObjective, ObjectiveType, QuestManager
   )

   # Create quest
   quest = Quest(
       name="Save the Village",
       description="Defeat the goblin raiders attacking the village",
       exp_reward=200,
       gold_reward=100
   )

   # Add objectives
   quest.add_objective(QuestObjective(
       description="Defeat Goblin Chief",
       objective_type=ObjectiveType.KILL_ENEMY,
       target="Goblin Chief",
       target_count=1
   ))

   quest.add_objective(QuestObjective(
       description="Collect village banner",
       objective_type=ObjectiveType.COLLECT_ITEM,
       target="Village Banner",
       target_count=1
   ))

   # Manage quests
   manager = QuestManager()
   manager.add_quest(quest)
   manager.start_quest(quest.id, game.events)

   # Update progress
   manager.update_objective(
       quest.id,
       ObjectiveType.KILL_ENEMY,
       "Goblin Chief",
       1,
       game.events
   )

Dialog System
-------------

Conversation Trees
~~~~~~~~~~~~~~~~~~

Create branching conversations with NPCs:

.. code-block:: python

   from barebones_rpg import DialogTree, DialogNode, DialogChoice

   tree = DialogTree(name="Merchant Conversation")

   greeting = DialogNode(
       id="greeting",
       speaker="Merchant",
       text="Welcome to my shop! What can I do for you?",
       choices=[
           DialogChoice(
               text="Show me your wares",
               next_node_id="shop"
           ),
           DialogChoice(
               text="Tell me about the town",
               next_node_id="town_info"
           ),
           DialogChoice(
               text="Goodbye",
               next_node_id=None
           )
       ]
   )

   tree.add_node(greeting)
   tree.set_start_node("greeting")

Dialog Sessions
~~~~~~~~~~~~~~~

Run dialog sessions with context:

.. code-block:: python

   from barebones_rpg import DialogSession

   session = DialogSession(tree, context={"player": hero})
   session.start()

   # Get current dialog
   current = session.get_current_node()
   print(f"{current.speaker}: {current.text}")

   # Get and present choices
   choices = session.get_available_choices()
   for i, choice in enumerate(choices):
       print(f"{i+1}. {choice.text}")

   # Player makes choice
   session.make_choice(0)

World and Maps
--------------

Location Management
~~~~~~~~~~~~~~~~~~~

Create and connect different areas:

.. code-block:: python

   from barebones_rpg import World, Location, Tile

   world = World(name="Fantasy Realm")

   # Create locations
   village = Location(name="Starting Village", width=30, height=30)
   dungeon = Location(name="Dark Dungeon", width=50, height=50)

   # Customize tiles
   for x in range(30):
       for y in range(30):
           tile = village.get_tile(x, y)
           if x == 0 or y == 0 or x == 29 or y == 29:
               tile.walkable = False
               tile.tile_type = "wall"

   # Connect locations
   world.add_location(village)
   world.add_location(dungeon)
   world.connect_locations(
       village.id, "north", dungeon.id,
       bidirectional=True
   )

   # Add entities to locations
   village.add_entity(merchant_npc, x=15, y=15)
   dungeon.add_entity(dragon_boss, x=25, y=25)

AI System
---------

Custom AI Implementation
~~~~~~~~~~~~~~~~~~~~~~~~

Implement custom AI for NPCs and enemies:

.. code-block:: python

   from barebones_rpg.entities import AIInterface, AIContext

   class AggressiveMeleeAI(AIInterface):
       def decide_action(self, context: AIContext) -> dict:
           """Make AI decision based on context.
           
           Returns a dict with 'action' key and action-specific data.
           """
           if context.nearby_entities:
               target = context.nearby_entities[0]
               # Get location from metadata
               location = context.metadata.get("location")
               
               distance = self._calculate_distance(
                   context.entity.position,
                   target.position
               )
               
               if distance <= 1:
                   return {
                       "action": "attack",
                       "target": target
                   }
               return {
                   "action": "move",
                   "position": target.position
               }
           
           return {"action": "wait"}

   # Create AI instance and assign directly to entity
   aggressive_ai = AggressiveMeleeAI()
   goblin = Enemy(name="Goblin", ai=aggressive_ai)

Save and Load
-------------

Persistent Game State
~~~~~~~~~~~~~~~~~~~~~

The framework includes comprehensive save/load functionality with automatic
callback registration:

.. code-block:: python

   from barebones_rpg import Game, GameConfig
   from barebones_rpg.items import create_consumable, LootManager

   # Define callback
   def heal_50(entity, context):
       entity.heal(50)
       return 50

   # Register item - callbacks are automatically registered for serialization
   health_potion = create_consumable(
       "Health Potion",
       on_use=heal_50,
       value=50
   )
   LootManager().register("Health Potion", health_potion)

   # Configure save directory
   config = GameConfig(save_directory="saves")
   game = Game(config)

   # Register objects
   game.register_entity(hero)
   game.register_item(magic_sword)
   game.register_quest(main_quest)

   # Save and load
   game.save_to_file("my_save")
   game.load_from_file("my_save")

   # Manage saves
   saves = game.list_saves()
   game.delete_save("old_save")

Next Steps
----------

- Explore the :doc:`tutorials/index` for detailed walkthroughs
- Read the :doc:`api/core` for complete API documentation
- Study the example games in the repository
- Check out :doc:`guides/index` for specific use cases

