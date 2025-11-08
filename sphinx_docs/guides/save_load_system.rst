Save/Load System Guide
======================

This guide explains how the save/load system works in Barebones RPG Framework, including
automatic callback serialization and best practices for managing game state.

Overview
--------

The framework provides a comprehensive save/load system that handles:

- **Automatic serialization** of entities, items, quests, and parties
- **Callback serialization** via symbolic names
- **Save file management** with versioning support
- **Custom data** through metadata dictionaries

Key Components
--------------

SaveManager
~~~~~~~~~~~

The ``SaveManager`` handles file I/O, directory management, and save versioning:

.. code-block:: python

   from barebones_rpg.core import Game, GameConfig
   
   # Configure save directory
   config = GameConfig(save_directory="my_saves")
   game = Game(config)
   
   # Save and load
   game.save_to_file("save_001")
   game.load_from_file("save_001")
   
   # List all saves
   saves = game.list_saves()
   for save_info in saves:
       print(f"{save_info['save_name']}: {save_info['timestamp']}")

CallbackRegistry
~~~~~~~~~~~~~~~~

The ``CallbackRegistry`` enables serialization of callback functions by mapping them to
symbolic names. This allows functions like ``on_use`` callbacks to be saved and restored.

**Important**: Callbacks must be registered before saving. The framework provides automatic
registration in specific cases (see below).

Automatic Callback Registration
--------------------------------

The framework automatically registers callbacks in two scenarios:

1. Items Registered with LootManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you register an item with ``LootManager``, its ``on_use`` callback is automatically
registered for serialization:

.. code-block:: python

   from barebones_rpg.items import create_consumable, LootManager
   
   def heal_50(entity, context):
       entity.heal(50)
       return 50
   
   # Create item with callback
   potion = create_consumable("Health Potion", on_use=heal_50)
   
   # Register with LootManager - callback is auto-registered!
   LootManager().register("health_potion", potion)
   
   # Now the callback can be serialized when saving

**What gets auto-registered**: Only the ``on_use`` callback from items registered with
``LootManager().register()``.

2. Quests Added to QuestManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you add a quest to ``QuestManager``, all its callbacks are automatically registered:

.. code-block:: python

   from barebones_rpg.quests import Quest, QuestObjective, QuestManager
   
   def quest_started(quest):
       print(f"Started: {quest.name}")
   
   def quest_completed(quest):
       print(f"Completed: {quest.name}")
   
   quest = Quest(
       name="My Quest",
       on_start=quest_started,
       on_complete=quest_completed
   )
   
   # Add to QuestManager - all callbacks auto-registered!
   QuestManager().add_quest(quest)

**What gets auto-registered**:
- Quest callbacks: ``on_start``, ``on_complete``, ``on_fail``
- Objective callbacks: ``condition``, ``on_progress``, ``on_complete``

Manual Callback Registration
-----------------------------

For items NOT registered with ``LootManager``, you must manually register callbacks:

.. code-block:: python

   from barebones_rpg.items import create_consumable
   from barebones_rpg.core.serialization import CallbackRegistry
   
   def poison_effect(entity, context):
       entity.take_damage(10)
       return -10
   
   # Create item directly (not via LootManager)
   poison = create_consumable("Poison Vial", on_use=poison_effect)
   
   # Manually register the callback for serialization
   CallbackRegistry.register("poison_effect", poison_effect)
   
   # Now add to inventory
   hero.inventory.add_item(poison)

When to Use Manual Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need manual registration when:

- Creating items directly without ``LootManager``
- Using custom callbacks not covered by auto-registration
- Building procedural/dynamic items at runtime

Best Practices
--------------

Recommended Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Use LootManager for reusable items**:

   .. code-block:: python
   
      # Register templates with LootManager
      LootManager().register("health_potion", health_potion_template)
      LootManager().register("sword", sword_template)
      
      # Get instances when needed
      drop = LootManager().get("health_potion")
      hero.inventory.add_item(drop)

2. **Use QuestManager for all quests**:

   .. code-block:: python
   
      quest = Quest(name="My Quest", on_complete=callback)
      QuestManager().add_quest(quest)  # Auto-registers callbacks

3. **Manual registration for edge cases**:

   .. code-block:: python
   
      # Only when you can't use LootManager or QuestManager
      CallbackRegistry.register("unique_callback", my_callback)

Common Patterns
~~~~~~~~~~~~~~~

**Pattern 1: Reusable Items**

.. code-block:: python

   # Define callbacks
   def heal_effect(entity, context):
       entity.heal(50)
   
   # Create and register with LootManager
   potion = create_consumable("Health Potion", on_use=heal_effect)
   LootManager().register("health_potion", potion)
   
   # Use throughout game
   loot_table = [
       {"item": "health_potion", "chance": 0.3}
   ]
   drops = roll_loot_table(loot_table)

**Pattern 2: Unique Items**

.. code-block:: python

   # For one-off items, still use LootManager
   def legendary_effect(entity, context):
       entity.stats.atk += 10
   
   legendary_sword = create_weapon(
       "Excalibur",
       base_damage=50,
       on_use=legendary_effect,
       unique=True
   )
   LootManager().register("excalibur", legendary_sword)
   
   # Get the unique instance
   sword = LootManager().get("excalibur")
   hero.inventory.add_item(sword)

**Pattern 3: Procedural Items**

.. code-block:: python

   # When generating items dynamically
   def random_potion_effect(entity, context):
       heal_amount = random.randint(30, 70)
       entity.heal(heal_amount)
       return heal_amount
   
   # Must manually register
   CallbackRegistry.register("random_potion_effect", random_potion_effect)
   
   # Create items at runtime
   for i in range(10):
       potion = create_consumable(
           f"Potion #{i}",
           on_use=random_potion_effect
       )
       hero.inventory.add_item(potion)

Complete Example
----------------

Here's a full example showing proper save/load setup:

.. code-block:: python

   from barebones_rpg.core import Game, GameConfig
   from barebones_rpg.items import create_consumable, create_weapon, LootManager
   from barebones_rpg.quests import Quest, QuestManager
   from barebones_rpg.entities import Character, Stats
   
   # 1. Define callbacks
   def heal_50(entity, context):
       entity.heal(50)
       return 50
   
   def quest_complete(quest):
       print(f"Completed: {quest.name}")
   
   # 2. Register items with LootManager (auto-registers callbacks)
   health_potion = create_consumable("Health Potion", on_use=heal_50, value=50)
   LootManager().register("health_potion", health_potion)
   
   iron_sword = create_weapon("Iron Sword", base_damage=10, value=100)
   LootManager().register("iron_sword", iron_sword)
   
   # 3. Create game
   config = GameConfig(save_directory="saves")
   game = Game(config)
   
   # 4. Create and register entities
   hero = Character(name="Hero", stats=Stats(hp=100, max_hp=100))
   hero.init_inventory()
   hero.inventory.add_item(LootManager().get("health_potion"))
   hero.inventory.add_item(LootManager().get("iron_sword"))
   game.register_entity(hero)
   
   # 5. Create and add quests (auto-registers callbacks)
   quest = Quest(name="First Quest", on_complete=quest_complete)
   QuestManager().add_quest(quest)
   
   # 6. Save and load
   game.save_to_file("my_save")
   print("Game saved!")
   
   # Later...
   game.load_from_file("my_save")
   print("Game loaded!")
   
   # Verify callback works
   restored_hero = game.get_entity_by_name("Hero")
   potion = restored_hero.inventory.items[0]
   potion.on_use(restored_hero, {})  # Callback still works!

Troubleshooting
---------------

Callback Not Restored After Load
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Item callbacks are ``None`` after loading.

**Solution**: Ensure callbacks are registered before saving:

.. code-block:: python

   # Option 1: Use LootManager (recommended)
   LootManager().register("my_item", item)
   
   # Option 2: Manual registration
   CallbackRegistry.register("my_callback", my_callback)

Save File Format
----------------

Save files are JSON with this structure:

.. code-block:: json

   {
       "version": "1.0",
       "timestamp": "2024-01-01T12:00:00",
       "entities": [...],
       "items": [...],
       "quests": [...],
       "parties": [...]
   }

Callbacks are stored as symbolic names:

.. code-block:: json

   {
       "name": "Health Potion",
       "on_use": "health_potion.on_use"
   }

On load, the ``CallbackRegistry`` maps ``"health_potion.on_use"`` back to the actual function.

Advanced Topics
---------------

Custom System Serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add save/load to custom systems:

.. code-block:: python

   class CustomSystem:
       def save(self) -> dict:
           """Return serializable state."""
           return {
               "my_data": self.my_data,
               "my_counter": self.counter
           }
       
       def load(self, data: dict) -> None:
           """Restore state from data."""
           self.my_data = data["my_data"]
           self.counter = data["my_counter"]
   
   # Register with game
   game.register_system("custom", custom_system)
   
   # Automatically saved/loaded with game

Migration Between Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handle save file version changes:

.. code-block:: python

   def migrate_save_v1_to_v2(data: dict) -> dict:
       """Migrate old save format to new."""
       # Add new fields with defaults
       for entity in data["entities"]:
           if "action_points" not in entity:
               entity["action_points"] = 10
       return data
   
   # Apply migration when loading
   if save_data["version"] == "1.0":
       save_data = migrate_save_v1_to_v2(save_data)

Summary
-------

**Key Takeaways**:

1. ✅ **Use ``LootManager``** for items with callbacks - auto-registers ``on_use``
2. ✅ **Use ``QuestManager.add_quest()``** for quests - auto-registers all callbacks
3. ⚠️ **Manual registration required** for items created directly without ``LootManager``
4. 🎯 **Best practice**: Use the managers whenever possible to avoid manual registration

**Quick Reference**:

.. code-block:: python

   # ✅ Good: Auto-registration
   LootManager().register("potion", potion)
   QuestManager().add_quest(quest)
   
   # ⚠️ Requires manual registration
   item = create_consumable("Custom", on_use=callback)
   CallbackRegistry.register("callback", callback)
   hero.inventory.add_item(item)
