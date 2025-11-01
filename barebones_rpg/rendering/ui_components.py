"""Common UI components for RPG games.

This module provides reusable UI components like resource bars,
turn indicators, quest displays, and instruction panels.
"""

from typing import Optional, List, Tuple, Any
from barebones_rpg.rendering.renderer import Renderer, Colors, Color
from barebones_rpg.quests.quest import QuestManager, Quest


class UIComponents:
    """Collection of reusable UI components.

    This class provides common UI elements that can be easily rendered
    in RPG games, such as turn indicators, resource bars, quest lists, etc.

    Args:
        renderer: The base renderer to use
    """

    def __init__(self, renderer: Renderer):
        """Initialize the UI components.

        Args:
            renderer: The base renderer to use
        """
        self.renderer = renderer

    def render_turn_indicator(
        self,
        is_player_turn: bool,
        position: Tuple[int, int],
        player_text: str = "YOUR TURN",
        enemy_text: str = "ENEMY TURN",
        font_size: int = 20,
    ):
        """Render a turn indicator showing whose turn it is.

        Args:
            is_player_turn: Whether it's the player's turn
            position: Position to render at (x, y)
            player_text: Text to show on player's turn
            enemy_text: Text to show on enemy's turn
            font_size: Font size for the text
        """
        text = player_text if is_player_turn else enemy_text
        color = Colors.GREEN if is_player_turn else Colors.RED

        self.renderer.draw_text(
            text, position[0], position[1], color, font_size=font_size
        )

    def render_resource_bar(
        self,
        label: str,
        current: int,
        maximum: int,
        position: Tuple[int, int],
        font_size: int = 20,
        text_color: Optional[Color] = None,
    ):
        """Render a resource bar (HP, MP, AP, etc.).

        Args:
            label: Label for the resource (e.g., "HP", "MP", "AP")
            current: Current value
            maximum: Maximum value
            position: Position to render at (x, y)
            font_size: Font size for the text
            text_color: Color for the text (default: white)
        """
        if text_color is None:
            text_color = Colors.WHITE

        text = f"{label}: {current}/{maximum}"
        self.renderer.draw_text(
            text, position[0], position[1], text_color, font_size=font_size
        )

    def render_resource_bar_with_fill(
        self,
        label: str,
        current: int,
        maximum: int,
        position: Tuple[int, int],
        bar_width: int = 100,
        bar_height: int = 20,
        font_size: int = 16,
        fill_color: Optional[Color] = None,
        bg_color: Optional[Color] = None,
    ):
        """Render a resource bar with a visual fill indicator.

        Args:
            label: Label for the resource
            current: Current value
            maximum: Maximum value
            position: Position to render at (x, y)
            bar_width: Width of the bar in pixels
            bar_height: Height of the bar in pixels
            font_size: Font size for the text
            fill_color: Color for the filled portion
            bg_color: Color for the background
        """
        if fill_color is None:
            fill_color = Colors.GREEN
        if bg_color is None:
            bg_color = Colors.DARK_GRAY

        x, y = position

        # Draw label
        self.renderer.draw_text(label, x, y, Colors.WHITE, font_size=font_size)

        # Draw bar background
        bar_x = x
        bar_y = y + font_size + 2
        self.renderer.draw_rect(
            bar_x, bar_y, bar_width, bar_height, bg_color, filled=True
        )

        # Draw filled portion
        fill_percent = current / maximum if maximum > 0 else 0
        fill_width = int(bar_width * fill_percent)
        self.renderer.draw_rect(
            bar_x, bar_y, fill_width, bar_height, fill_color, filled=True
        )

        # Draw border
        self.renderer.draw_rect(
            bar_x, bar_y, bar_width, bar_height, Colors.WHITE, filled=False
        )

        # Draw text on bar
        text = f"{current}/{maximum}"
        text_width = len(text) * 6
        text_x = bar_x + (bar_width - text_width) // 2
        text_y = bar_y + (bar_height - font_size) // 2
        self.renderer.draw_text(text, text_x, text_y, Colors.WHITE, font_size=font_size)

    def render_quest_list(
        self,
        quest_manager: QuestManager,
        position: Tuple[int, int],
        max_quests: Optional[int] = None,
        show_objectives: bool = True,
        title: str = "Active Quests:",
        title_font_size: int = 16,
        quest_font_size: int = 14,
        objective_font_size: int = 12,
    ):
        """Render a list of active quests with objectives.

        Args:
            quest_manager: The quest manager containing quests
            position: Position to render at (x, y)
            max_quests: Maximum number of quests to show (None = all)
            show_objectives: Whether to show objectives
            title: Title text
            title_font_size: Font size for the title
            quest_font_size: Font size for quest names
            objective_font_size: Font size for objectives
        """
        x, y = position
        current_y = y

        active_quests = quest_manager.get_active_quests()

        if not active_quests:
            return

        # Draw title
        self.renderer.draw_text(
            title, x, current_y, Colors.YELLOW, font_size=title_font_size
        )
        current_y += title_font_size + 4

        # Limit number of quests if specified
        quests_to_show = active_quests[:max_quests] if max_quests else active_quests

        for quest in quests_to_show:
            # Draw quest name
            self.renderer.draw_text(
                f"- {quest.name}",
                x + 5,
                current_y,
                Colors.WHITE,
                font_size=quest_font_size,
            )
            current_y += quest_font_size + 4

            # Draw objectives if requested
            if show_objectives:
                for objective in quest.objectives:
                    status_text = (
                        "✓"
                        if objective.is_completed()
                        else f"({objective.get_progress_text()})"
                    )
                    obj_color = (
                        Colors.GREEN if objective.is_completed() else Colors.LIGHT_GRAY
                    )

                    self.renderer.draw_text(
                        f"  {status_text} {objective.description}",
                        x + 10,
                        current_y,
                        obj_color,
                        font_size=objective_font_size,
                    )
                    current_y += objective_font_size + 2

    def render_instructions(
        self,
        instructions: List[str],
        position: Tuple[int, int],
        font_size: int = 12,
        line_spacing: int = 15,
        text_color: Optional[Color] = None,
    ):
        """Render a list of instruction text.

        Args:
            instructions: List of instruction strings
            position: Position to render at (x, y)
            font_size: Font size for the text
            line_spacing: Spacing between lines in pixels
            text_color: Color for the text (default: light gray)
        """
        if text_color is None:
            text_color = Colors.LIGHT_GRAY

        x, y = position

        for i, instruction in enumerate(instructions):
            self.renderer.draw_text(
                instruction, x, y + i * line_spacing, text_color, font_size=font_size
            )

    def render_message_log(
        self,
        messages: List[str],
        position: Tuple[int, int],
        max_messages: int = 10,
        font_size: int = 14,
        line_spacing: int = 20,
        text_color: Optional[Color] = None,
    ):
        """Render a message log (e.g., combat log).

        Args:
            messages: List of message strings
            position: Position to render at (x, y)
            max_messages: Maximum number of messages to show
            font_size: Font size for the text
            line_spacing: Spacing between lines in pixels
            text_color: Color for the text (default: white)
        """
        if text_color is None:
            text_color = Colors.WHITE

        x, y = position

        # Show only the most recent messages
        visible_messages = (
            messages[-max_messages:] if len(messages) > max_messages else messages
        )

        for i, message in enumerate(visible_messages):
            self.renderer.draw_text(
                message, x, y + i * line_spacing, text_color, font_size=font_size
            )

    def render_stat_panel(
        self,
        entity: Any,
        position: Tuple[int, int],
        show_name: bool = True,
        show_hp: bool = True,
        show_mp: bool = True,
        show_atk: bool = True,
        show_def: bool = True,
        name_font_size: int = 20,
        stat_font_size: int = 16,
        line_spacing: int = 20,
    ):
        """Render a stat panel for an entity.

        Args:
            entity: Entity to show stats for (must have stats attribute)
            position: Position to render at (x, y)
            show_name: Whether to show entity name
            show_hp: Whether to show HP
            show_mp: Whether to show MP
            show_atk: Whether to show attack
            show_def: Whether to show defense
            name_font_size: Font size for the name
            stat_font_size: Font size for stats
            line_spacing: Spacing between lines
        """
        if not hasattr(entity, "stats"):
            return

        x, y = position
        current_y = y

        # Determine color based on faction
        name_color = Colors.BLUE
        if hasattr(entity, "faction"):
            if entity.faction == "enemy":
                name_color = Colors.RED
            elif entity.faction == "neutral":
                name_color = Colors.GREEN

        # Draw name
        if show_name and hasattr(entity, "name"):
            self.renderer.draw_text(
                entity.name, x, current_y, name_color, font_size=name_font_size
            )
            current_y += name_font_size + 5

        # Draw stats
        if show_hp:
            self.renderer.draw_text(
                f"HP: {entity.stats.hp}/{entity.stats.max_hp}",
                x,
                current_y,
                Colors.WHITE,
                font_size=stat_font_size,
            )
            current_y += line_spacing

        if show_mp:
            self.renderer.draw_text(
                f"MP: {entity.stats.mp}/{entity.stats.max_mp}",
                x,
                current_y,
                Colors.WHITE,
                font_size=stat_font_size,
            )
            current_y += line_spacing

        if show_atk:
            self.renderer.draw_text(
                f"STR: {entity.stats.strength}",
                x,
                current_y,
                Colors.WHITE,
                font_size=stat_font_size,
            )
            current_y += line_spacing

        if show_def:
            self.renderer.draw_text(
                f"DEF: {entity.stats.physical_defense}",
                x,
                current_y,
                Colors.WHITE,
                font_size=stat_font_size,
            )
            current_y += line_spacing

    def render_title_screen_text(
        self,
        title: str,
        position: Tuple[int, int],
        font_size: int = 32,
        color: Optional[Color] = None,
    ):
        """Render large title text.

        Args:
            title: Title text
            position: Position to render at (x, y)
            font_size: Font size for the title
            color: Color for the text (default: white)
        """
        if color is None:
            color = Colors.WHITE

        self.renderer.draw_text(
            title, position[0], position[1], color, font_size=font_size
        )

    def render_button(
        self,
        text: str,
        position: Tuple[int, int],
        width: int,
        height: int,
        is_hovered: bool = False,
        bg_color: Optional[Color] = None,
        hover_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        font_size: int = 16,
    ):
        """Render a button with hover effect.

        Args:
            text: Button text
            position: Position to render at (x, y)
            width: Button width
            height: Button height
            is_hovered: Whether the button is being hovered
            bg_color: Background color (default: dark gray)
            hover_color: Hover background color (default: lighter gray)
            text_color: Text color (default: white)
            font_size: Font size for the text
        """
        if bg_color is None:
            bg_color = Color(50, 50, 70)
        if hover_color is None:
            hover_color = Color(80, 80, 120)
        if text_color is None:
            text_color = Colors.WHITE

        x, y = position

        # Draw button background
        color = hover_color if is_hovered else bg_color
        self.renderer.draw_rect(x, y, width, height, color, filled=True)
        self.renderer.draw_rect(x, y, width, height, Colors.WHITE, filled=False)

        # Draw button text (centered)
        text_width = len(text) * (font_size // 2)
        text_x = x + (width - text_width) // 2
        text_y = y + (height - font_size) // 2

        self.renderer.draw_text(text, text_x, text_y, text_color, font_size=font_size)
