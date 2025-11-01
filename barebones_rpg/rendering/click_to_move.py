"""Click-to-move handler for tile-based games.

This module provides an input handler for click-based movement on tile maps,
including hover effects, path previews, and click handling.
"""

from typing import Optional, Set, Tuple, List, Callable, Any
import pygame

from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder


class ClickToMoveHandler:
    """Handler for click-to-move input on tile-based maps.

    This class manages:
    - Mouse hover tracking
    - Path preview calculation
    - Click detection and tile selection
    - Callbacks for movement and interaction

    Args:
        tile_size: Size of each tile in pixels
        grid_width: Width of the grid in tiles
        grid_height: Height of the grid in tiles
        pathfinder: Optional pathfinder for path previews
    """

    def __init__(
        self,
        tile_size: int,
        grid_width: int,
        grid_height: int,
        pathfinder: Optional[TilemapPathfinder] = None,
    ):
        """Initialize the click-to-move handler.

        Args:
            tile_size: Size of each tile in pixels
            grid_width: Width of the grid in tiles
            grid_height: Height of the grid in tiles
            pathfinder: Optional pathfinder for path previews
        """
        self.tile_size = tile_size
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.pathfinder = pathfinder

        self.hover_tile: Optional[Tuple[int, int]] = None
        self.path_preview: List[Tuple[int, int]] = []

        # Callbacks
        self.on_tile_clicked: Optional[Callable[[Tuple[int, int]], None]] = None
        self.on_entity_clicked: Optional[Callable[[Any], None]] = None

    def set_pathfinder(self, pathfinder: TilemapPathfinder):
        """Set or update the pathfinder for path previews.

        Args:
            pathfinder: The pathfinder to use
        """
        self.pathfinder = pathfinder

    def screen_to_tile(self, screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """Convert screen coordinates to tile coordinates.

        Args:
            screen_x: Screen X coordinate in pixels
            screen_y: Screen Y coordinate in pixels

        Returns:
            Tile coordinates (x, y) or None if out of bounds
        """
        grid_x = screen_x // self.tile_size
        grid_y = screen_y // self.tile_size

        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return (grid_x, grid_y)
        return None

    def handle_mouse_motion(
        self,
        event: pygame.event.Event,
        valid_moves: Optional[Set[Tuple[int, int]]] = None,
        current_position: Optional[Tuple[int, int]] = None,
    ):
        """Handle mouse motion events to update hover and path preview.

        Args:
            event: Pygame mouse motion event
            valid_moves: Set of valid movement tiles (for path preview)
            current_position: Current position to path from
        """
        mouse_x, mouse_y = event.pos
        tile_pos = self.screen_to_tile(mouse_x, mouse_y)

        if tile_pos:
            self.hover_tile = tile_pos

            # Calculate path preview if hovering over valid tile
            if (
                valid_moves
                and tile_pos in valid_moves
                and current_position
                and self.pathfinder
            ):
                self.path_preview = self.pathfinder.find_path(
                    current_position, tile_pos
                )
            else:
                self.path_preview = []
        else:
            self.hover_tile = None
            self.path_preview = []

    def handle_mouse_click(
        self,
        event: pygame.event.Event,
        get_entity_at: Optional[Callable[[int, int], Any]] = None,
    ) -> Optional[Tuple[int, int]]:
        """Handle mouse click events.

        Args:
            event: Pygame mouse button event
            get_entity_at: Optional function to get entity at position

        Returns:
            Clicked tile position or None
        """
        mouse_x, mouse_y = event.pos
        tile_pos = self.screen_to_tile(mouse_x, mouse_y)

        if tile_pos:
            # Check if clicking on an entity
            if get_entity_at:
                entity = get_entity_at(tile_pos[0], tile_pos[1])
                if entity and self.on_entity_clicked:
                    self.on_entity_clicked(entity)
                    return None

            # Trigger tile clicked callback
            if self.on_tile_clicked:
                self.on_tile_clicked(tile_pos)

            return tile_pos

        return None

    def get_hover_tile(self) -> Optional[Tuple[int, int]]:
        """Get the currently hovered tile.

        Returns:
            Hovered tile position or None
        """
        return self.hover_tile

    def get_path_preview(self) -> List[Tuple[int, int]]:
        """Get the current path preview.

        Returns:
            List of tile positions in the preview path
        """
        return self.path_preview

    def clear_hover(self):
        """Clear hover state and path preview."""
        self.hover_tile = None
        self.path_preview = []


class TileInteractionHandler:
    """Higher-level handler for tile-based interactions.

    This combines ClickToMoveHandler with logic for handling different
    types of interactions (movement, attacking, talking to NPCs, etc.)

    Args:
        click_handler: The click-to-move handler to use
    """

    def __init__(self, click_handler: ClickToMoveHandler):
        """Initialize the interaction handler.

        Args:
            click_handler: The click-to-move handler to use
        """
        self.click_handler = click_handler

        # Interaction callbacks
        self.on_move: Optional[Callable[[Tuple[int, int]], None]] = None
        self.on_attack_enemy: Optional[Callable[[Any], None]] = None
        self.on_interact_npc: Optional[Callable[[Any], None]] = None
        self.on_interact_item: Optional[Callable[[Any], None]] = None

    def handle_tile_click(
        self,
        tile_pos: Tuple[int, int],
        entity_at_tile: Optional[Any],
        valid_moves: Set[Tuple[int, int]],
    ):
        """Handle a tile click with interaction logic.

        Args:
            tile_pos: The clicked tile position
            entity_at_tile: Entity at the clicked position (if any)
            valid_moves: Set of valid movement tiles
        """
        if entity_at_tile:
            # Clicked on an entity - determine interaction type
            if hasattr(entity_at_tile, "faction"):
                if entity_at_tile.faction == "enemy" and self.on_attack_enemy:
                    self.on_attack_enemy(entity_at_tile)
                elif (
                    entity_at_tile.faction in ["neutral", "friendly"]
                    and self.on_interact_npc
                ):
                    self.on_interact_npc(entity_at_tile)
        elif tile_pos in valid_moves and self.on_move:
            # Valid movement tile
            self.on_move(tile_pos)

    def set_callbacks(
        self,
        on_move: Optional[Callable[[Tuple[int, int]], None]] = None,
        on_attack_enemy: Optional[Callable[[Any], None]] = None,
        on_interact_npc: Optional[Callable[[Any], None]] = None,
        on_interact_item: Optional[Callable[[Any], None]] = None,
    ):
        """Set interaction callbacks.

        Args:
            on_move: Callback when player moves to a tile
            on_attack_enemy: Callback when player attacks an enemy
            on_interact_npc: Callback when player interacts with NPC
            on_interact_item: Callback when player interacts with item
        """
        if on_move:
            self.on_move = on_move
        if on_attack_enemy:
            self.on_attack_enemy = on_attack_enemy
        if on_interact_npc:
            self.on_interact_npc = on_interact_npc
        if on_interact_item:
            self.on_interact_item = on_interact_item
