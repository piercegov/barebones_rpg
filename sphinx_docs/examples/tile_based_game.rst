Tile-Based Game Example
=======================

An advanced example demonstrating tile-based gameplay with click-to-move, pathfinding, and action points.

Overview
--------

This example showcases:

- Grid-based tile map
- Click-to-move with pathfinding
- Action point system
- Turn-based movement and combat
- Visual tile renderer
- Enemy AI

Running the Example
-------------------

.. code-block:: bash

   # Run the tile-based example
   uv run python -m barebones_rpg.examples.tile_based_example

   # Or directly
   python -m barebones_rpg.examples.tile_based_example

Features
--------

Tile-Based Movement
~~~~~~~~~~~~~~~~~~~

- Click on tiles to move your character
- Pathfinding automatically routes around obstacles
- Movement costs action points

Action Point System
~~~~~~~~~~~~~~~~~~~

- Each turn has limited action points
- Moving costs points based on distance
- Attacking costs action points
- Plan your moves strategically

Visual Feedback
~~~~~~~~~~~~~~~

- Tiles highlight on hover
- Path preview when planning movement
- Visual indicators for walkable/blocked tiles
- Entity sprites on the grid

Enemy AI
~~~~~~~~

Enemies use AI to:

- Detect nearby players
- Path-find to targets
- Make strategic decisions
- Manage their action points

Technical Implementation
------------------------

Tilemap Setup
~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.world import Location, Tile

   location = Location(name="Battle Arena", width=40, height=30)

   # Set up terrain
   for x in range(40):
       for y in range(30):
           tile = location.get_tile(x, y)
           
           # Create walls around edges
           if x == 0 or y == 0 or x == 39 or y == 29:
               tile.walkable = False
               tile.tile_type = "wall"
           else:
               tile.walkable = True
               tile.tile_type = "floor"

Click-to-Move System
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.rendering import ClickToMoveHandler

   click_handler = ClickToMoveHandler(
       location=location,
       tile_renderer=tile_renderer
   )

   # In game loop
   if mouse_clicked:
       tile_x, tile_y = get_clicked_tile(mouse_pos)
       path = click_handler.handle_click(
           entity=hero,
           target_x=tile_x,
           target_y=tile_y
       )
       
       if path:
           move_along_path(hero, path)

Action Points
~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.world import APManager

   ap_manager = APManager(max_ap=10)

   # Start turn
   ap_manager.reset_points()

   # Perform actions
   if ap_manager.can_perform_action(move_cost):
       ap_manager.spend_points(move_cost)
       move_entity(hero, new_x, new_y)

   # Check remaining points
   remaining = ap_manager.get_remaining_points()

Pathfinding
~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.world import TilemapPathfinder

   pathfinder = TilemapPathfinder(location)

   # Find path from start to goal
   path = pathfinder.find_path(
       start_x=hero.position[0],
       start_y=hero.position[1],
       goal_x=target_x,
       goal_y=target_y
   )

   if path:
       # path is a list of (x, y) coordinates
       for x, y in path:
           move_to(x, y)

AI Integration
~~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.entities import AIInterface, AIContext

   class TacticalTileAI(AIInterface):
       def decide_action(self, context: AIContext) -> dict:
           """Make decisions based on tile positions.
           
           Returns a dict with 'action' key and action-specific data.
           """
           entity = context.entity
           targets = context.nearby_entities
           
           if not targets:
               return {"action": "wait"}
           
           target = targets[0]
           
           # Calculate tile distance
           distance = abs(entity.position[0] - target.position[0]) + \
                     abs(entity.position[1] - target.position[1])
           
           # Attack if in range
           if distance <= 1:
               if context.metadata.get("ap", 0) >= 3:
                   return {
                       "action": "attack",
                       "target": target,
                       "ap_cost": 3
                   }
           
           # Move closer
           path = find_path(entity.position, target.position)
           if path and len(path) > 1:
               next_pos = path[1]
               return {
                   "action": "move",
                   "position": next_pos,
                   "ap_cost": 1
               }
           
           return {"action": "wait"}
   
   # Create AI instance and assign to entity
   tactical_ai = TacticalTileAI()
   goblin = Enemy(name="Goblin", ai=tactical_ai)

Rendering System
~~~~~~~~~~~~~~~~

.. code-block:: python

   from barebones_rpg.rendering import TileRenderer

   tile_renderer = TileRenderer(
       renderer=pygame_renderer,
       tile_width=32,
       tile_height=32,
       camera_width=25,
       camera_height=18
   )

   # Render the map
   tile_renderer.render_location(
       location=location,
       camera_x=camera_x,
       camera_y=camera_y,
       entities=all_entities
   )

Game Loop Structure
-------------------

.. code-block:: python

   def game_loop():
       running = True
       
       while running:
           # Handle input
           for event in pygame.event.get():
               if event.type == pygame.MOUSEBUTTONDOWN:
                   handle_click(event.pos)
           
           # Update game state
           if current_state == CombatState.PLAYER_TURN:
               # Handle player input
               pass
           elif current_state == CombatState.ENEMY_TURN:
               # Execute enemy AI
               for enemy in enemies:
                   ai_action = enemy.ai.decide_action(context)
                   execute_action(ai_action)
           
           # Render
           renderer.clear()
           tile_renderer.render_location(location, camera_x, camera_y)
           renderer.present()

Key Learning Points
-------------------

1. **Spatial Game Design**: Grid-based positioning and movement
2. **Resource Management**: Action point economy
3. **Pathfinding Algorithms**: A* implementation for tile maps
4. **AI Decision Making**: Context-aware AI behavior
5. **Camera System**: Viewport management for large maps
6. **Input Handling**: Mouse interaction with game world

Customization Ideas
-------------------

Try modifying the example:

- Add different terrain types (water, forest, mountains)
- Implement fog of war
- Create special tile effects (damage tiles, healing tiles)
- Add ranged attacks with line-of-sight
- Implement cover mechanics
- Create destructible tiles

Next Steps
----------

- Study the full source in ``barebones_rpg/examples/tile_based_example.py``
- Learn about :doc:`../api/world` for world management
- Read :doc:`../api/rendering` for rendering systems
- Explore :doc:`../guides/custom_ai` for advanced AI

