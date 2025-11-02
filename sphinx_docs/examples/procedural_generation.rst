Procedural Generation
=====================

Learn how to create dynamically generated content for endless replayability.

Coming Soon
-----------

This guide is under development and will cover:

- Procedural dungeon generation
- Random enemy spawning
- Dynamic loot tables
- Procedural quest generation
- Name generators
- Balanced stat generation

Example Snippet
---------------

.. code-block:: python

   import random
   from barebones_rpg import Enemy, Stats, Location

   def generate_enemy(level, enemy_type=None):
       """Generate a random enemy scaled to level."""
       types = ["Goblin", "Orc", "Troll", "Dragon", "Skeleton"]
       enemy_type = enemy_type or random.choice(types)
       
       # Scale attributes based on level
       base_str = 8 + level * 2
       base_con = 6 + level * 2
       base_dex = 10 + random.randint(-2, 2)
       
       return Enemy(
           name=f"Level {level} {enemy_type}",
           stats=Stats(
               strength=base_str,
               constitution=base_con,
               dexterity=base_dex,
               intelligence=5 + level,
               charisma=5,
               base_max_hp=20 + level * 10,
               hp=30 + level * 15
           ),
           exp_reward=level * 25,
           gold_reward=level * 10
       )

   def generate_dungeon_floor(floor_number):
       """Generate a random dungeon floor."""
       width, height = 40, 30
       location = Location(
           name=f"Dungeon Floor {floor_number}",
           width=width,
           height=height
       )
       
       # Place walls randomly
       num_walls = random.randint(20, 40)
       for _ in range(num_walls):
           x = random.randint(1, width - 2)
           y = random.randint(1, height - 2)
           tile = location.get_tile(x, y)
           tile.walkable = False
           tile.tile_type = "wall"
       
       # Spawn enemies
       num_enemies = 3 + floor_number
       enemies = []
       for _ in range(num_enemies):
           enemy = generate_enemy(floor_number)
           x = random.randint(1, width - 2)
           y = random.randint(1, height - 2)
           location.add_entity(enemy, x, y)
           enemies.append(enemy)
       
       return location, enemies

Check back soon for the complete guide!

