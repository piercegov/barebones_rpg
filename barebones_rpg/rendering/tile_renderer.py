"""Tile-based rendering utilities.

This module provides rendering helpers specifically for tile-based maps,
including grid rendering, entity rendering, and visual effects like
movement highlights and path previews.
"""

from typing import Optional, Set, Tuple, List
from barebones_rpg.rendering.renderer import Renderer, Colors, Color
from barebones_rpg.world.world import Location
from barebones_rpg.entities.entity import Entity


class TileRenderer:
    """Renderer for tile-based maps and entities.

    This class handles rendering of:
    - Tile grids with borders
    - Movement range highlights
    - Path previews
    - Hover effects
    - Entities on tiles
    - Entity HP bars

    Args:
        renderer: The base renderer to use for drawing
        tile_size: Size of each tile in pixels (default: 32)
    """

    def __init__(self, renderer: Renderer, tile_size: int = 32):
        """Initialize the tile renderer.

        Args:
            renderer: The base renderer to use for drawing
            tile_size: Size of each tile in pixels
        """
        self.renderer = renderer
        self.tile_size = tile_size

    def render_tile_grid(
        self,
        location: Location,
        walkable_color: Optional[Color] = None,
        wall_color: Optional[Color] = None,
        grid_line_color: Optional[Color] = None,
    ):
        """Render the tile grid for a location.

        Args:
            location: The location to render
            walkable_color: Color for walkable tiles (default: dark gray)
            wall_color: Color for non-walkable tiles (default: darker gray)
            grid_line_color: Color for grid lines (default: medium gray)
        """
        if walkable_color is None:
            walkable_color = Colors.DARK_GRAY
        if wall_color is None:
            wall_color = Color(40, 40, 40)
        if grid_line_color is None:
            grid_line_color = Color(60, 60, 60)

        for y in range(location.height):
            for x in range(location.width):
                tile = location.get_tile(x, y)
                screen_x = x * self.tile_size
                screen_y = y * self.tile_size

                # Tile background
                color = walkable_color if tile and tile.walkable else wall_color
                self.renderer.draw_rect(
                    screen_x,
                    screen_y,
                    self.tile_size,
                    self.tile_size,
                    color,
                    filled=True,
                )

                # Grid lines
                self.renderer.draw_rect(
                    screen_x,
                    screen_y,
                    self.tile_size,
                    self.tile_size,
                    grid_line_color,
                    filled=False,
                )

    def render_movement_highlights(
        self,
        valid_moves: Set[Tuple[int, int]],
        current_position: Optional[Tuple[int, int]] = None,
        highlight_color: Optional[Color] = None,
        padding: int = 2,
    ):
        """Render highlights for valid movement tiles.

        Args:
            valid_moves: Set of valid move positions
            current_position: Position to exclude from highlighting (usually current position)
            highlight_color: Color for the highlight (default: blue)
            padding: Padding from tile edges in pixels
        """
        if highlight_color is None:
            highlight_color = Color(100, 100, 255)

        for pos in valid_moves:
            if current_position and pos == current_position:
                continue

            screen_x = pos[0] * self.tile_size
            screen_y = pos[1] * self.tile_size

            self.renderer.draw_rect(
                screen_x + padding,
                screen_y + padding,
                self.tile_size - padding * 2,
                self.tile_size - padding * 2,
                highlight_color,
                filled=True,
            )

    def render_path_preview(
        self,
        path: List[Tuple[int, int]],
        skip_first: bool = True,
        path_color: Optional[Color] = None,
        padding: int = 4,
    ):
        """Render a path preview showing movement trajectory.

        Args:
            path: List of positions in the path
            skip_first: Whether to skip rendering the first position (current position)
            path_color: Color for the path (default: light blue)
            padding: Padding from tile edges in pixels
        """
        if path_color is None:
            path_color = Color(200, 200, 255)

        start_index = 1 if skip_first else 0

        for i in range(start_index, len(path)):
            pos = path[i]
            screen_x = pos[0] * self.tile_size
            screen_y = pos[1] * self.tile_size

            self.renderer.draw_rect(
                screen_x + padding,
                screen_y + padding,
                self.tile_size - padding * 2,
                self.tile_size - padding * 2,
                path_color,
                filled=True,
            )

    def render_hover_highlight(
        self, position: Tuple[int, int], hover_color: Optional[Color] = None
    ):
        """Render a hover highlight on a tile.

        Args:
            position: The tile position to highlight
            hover_color: Color for the hover effect (default: yellow)
        """
        if hover_color is None:
            hover_color = Colors.YELLOW

        screen_x = position[0] * self.tile_size
        screen_y = position[1] * self.tile_size

        self.renderer.draw_rect(
            screen_x,
            screen_y,
            self.tile_size,
            self.tile_size,
            hover_color,
            filled=False,
        )

    def render_entity(
        self,
        entity: Entity,
        faction_colors: Optional[dict] = None,
        draw_name: bool = True,
        draw_hp_bar: bool = True,
    ):
        """Render an entity on a tile.

        Args:
            entity: The entity to render
            faction_colors: Dict mapping faction names to colors (optional)
            draw_name: Whether to draw the entity's name
            draw_hp_bar: Whether to draw the entity's HP bar
        """
        if faction_colors is None:
            faction_colors = {
                "player": Colors.BLUE,
                "enemy": Colors.RED,
                "neutral": Colors.GREEN,
            }

        x, y = entity.position
        screen_x = x * self.tile_size + self.tile_size // 2
        screen_y = y * self.tile_size + self.tile_size // 2
        radius = self.tile_size // 3

        # Get color based on faction
        color = faction_colors.get(entity.faction, Colors.WHITE)

        # Draw circle for entity
        self.renderer.draw_circle(screen_x, screen_y, radius, color)

        # Draw name above entity
        if draw_name:
            name_width = len(entity.name) * 6
            self.renderer.draw_text(
                entity.name,
                screen_x - name_width // 2,
                screen_y - self.tile_size // 2 - 10,
                Colors.WHITE,
                font_size=14,
            )

        # Draw HP bar
        if draw_hp_bar and hasattr(entity, "stats"):
            self.render_entity_hp_bar(entity)

    def render_entity_hp_bar(
        self,
        entity: Entity,
        bar_height: int = 4,
        padding: int = 2,
        bg_color: Optional[Color] = None,
        hp_color: Optional[Color] = None,
    ):
        """Render an HP bar for an entity.

        Args:
            entity: The entity to render HP bar for
            bar_height: Height of the HP bar in pixels
            padding: Padding from tile edges
            bg_color: Background color (default: red)
            hp_color: HP fill color (default: green)
        """
        if bg_color is None:
            bg_color = Colors.RED
        if hp_color is None:
            hp_color = Colors.GREEN

        if not hasattr(entity, "stats"):
            return

        x, y = entity.position
        hp_percent = entity.stats.hp / entity.stats.max_hp

        bar_width = self.tile_size - padding * 2
        bar_x = x * self.tile_size + padding
        bar_y = y * self.tile_size + self.tile_size - bar_height - padding

        # Background
        self.renderer.draw_rect(
            bar_x, bar_y, bar_width, bar_height, bg_color, filled=True
        )

        # HP fill
        self.renderer.draw_rect(
            bar_x, bar_y, int(bar_width * hp_percent), bar_height, hp_color, filled=True
        )

    def render_location(
        self,
        location: Location,
        valid_moves: Optional[Set[Tuple[int, int]]] = None,
        path_preview: Optional[List[Tuple[int, int]]] = None,
        hover_tile: Optional[Tuple[int, int]] = None,
        current_entity_position: Optional[Tuple[int, int]] = None,
        draw_entity_names: bool = True,
        draw_entity_hp_bars: bool = True,
    ):
        """Render a complete location with all entities and effects.

        This is a convenience method that renders everything in the correct order.

        Args:
            location: The location to render
            valid_moves: Set of valid move positions to highlight
            path_preview: Path to preview
            hover_tile: Tile being hovered over
            current_entity_position: Position of current entity (excluded from highlights)
            draw_entity_names: Whether to draw entity names
            draw_entity_hp_bars: Whether to draw entity HP bars
        """
        # Draw tile grid
        self.render_tile_grid(location)

        # Draw movement highlights
        if valid_moves:
            self.render_movement_highlights(
                valid_moves, current_position=current_entity_position
            )

        # Draw path preview
        if path_preview:
            self.render_path_preview(path_preview)

        # Draw hover highlight
        if hover_tile:
            self.render_hover_highlight(hover_tile)

        # Draw entities
        for entity in location.entities:
            self.render_entity(
                entity, draw_name=draw_entity_names, draw_hp_bar=draw_entity_hp_bars
            )

    def screen_to_tile(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to tile coordinates.

        Args:
            screen_x: Screen X coordinate in pixels
            screen_y: Screen Y coordinate in pixels

        Returns:
            Tile coordinates (grid_x, grid_y)
        """
        return (screen_x // self.tile_size, screen_y // self.tile_size)

    def tile_to_screen(self, tile_x: int, tile_y: int) -> Tuple[int, int]:
        """Convert tile coordinates to screen coordinates (top-left of tile).

        Args:
            tile_x: Tile X coordinate
            tile_y: Tile Y coordinate

        Returns:
            Screen coordinates (screen_x, screen_y)
        """
        return (tile_x * self.tile_size, tile_y * self.tile_size)

    def tile_to_screen_center(self, tile_x: int, tile_y: int) -> Tuple[int, int]:
        """Convert tile coordinates to screen coordinates (center of tile).

        Args:
            tile_x: Tile X coordinate
            tile_y: Tile Y coordinate

        Returns:
            Screen coordinates at center of tile (screen_x, screen_y)
        """
        return (
            tile_x * self.tile_size + self.tile_size // 2,
            tile_y * self.tile_size + self.tile_size // 2,
        )
