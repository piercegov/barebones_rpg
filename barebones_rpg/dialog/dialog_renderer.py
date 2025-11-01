"""Dialog UI rendering utilities.

This module provides rendering utilities for dialog trees, including
dialog boxes, speaker names, text with word wrapping, and choice buttons.
"""

from typing import Optional, Tuple
import pygame

from barebones_rpg.dialog.dialog import DialogSession
from barebones_rpg.rendering.renderer import Renderer, Colors, Color


class DialogRenderer:
    """Renderer for dialog UI.

    This class handles rendering of:
    - Dialog boxes with borders
    - Speaker names
    - Dialog text with word wrapping
    - Choice buttons with hover effects
    - Click handling for choices

    Args:
        renderer: The base renderer to use
        screen_width: Width of the screen in pixels
        screen_height: Height of the screen in pixels
    """

    def __init__(self, renderer: Renderer, screen_width: int, screen_height: int):
        """Initialize the dialog renderer.

        Args:
            renderer: The base renderer to use
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels
        """
        self.renderer = renderer
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Configurable dimensions
        self.dialog_box_height = 400
        self.dialog_box_margin = 20
        self.dialog_box_padding = 20
        self.choice_height = 40
        self.choice_padding = 10
        self.choice_width = 500
        self.choice_y_start_offset = 180
        self.text_y_offset = 60
        self.text_line_spacing = 22

        # Font sizes
        self.speaker_font_size = 20
        self.text_font_size = 16
        self.choice_font_size = 16

        # Colors
        self.bg_color = Color(30, 30, 40)
        self.border_color = Colors.WHITE
        self.speaker_color = Colors.YELLOW
        self.text_color = Colors.WHITE
        self.choice_bg_color = Color(50, 50, 70)
        self.choice_hover_color = Color(80, 80, 120)

    def wrap_text(self, text: str, max_width: int, char_width: int = 8) -> list[str]:
        """Wrap text to fit within a maximum width.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            char_width: Approximate character width in pixels

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []
        current_width = 0

        for word in words:
            word_width = len(word) * char_width
            if current_width + word_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width + char_width

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def get_dialog_box_bounds(self) -> Tuple[int, int, int, int]:
        """Get the bounds of the dialog box.

        Returns:
            Tuple of (x, y, width, height)
        """
        width = self.screen_width - self.dialog_box_margin * 2
        height = self.dialog_box_height
        x = self.dialog_box_margin
        y = self.screen_height - height - self.dialog_box_margin

        return (x, y, width, height)

    def get_choice_bounds(
        self, choice_index: int, num_choices: int
    ) -> Tuple[int, int, int, int]:
        """Get the bounds of a choice button.

        Args:
            choice_index: Index of the choice
            num_choices: Total number of choices

        Returns:
            Tuple of (x, y, width, height)
        """
        dialog_x, dialog_y, dialog_width, dialog_height = self.get_dialog_box_bounds()

        # Choices start below the text area
        choice_y_start = dialog_y + self.choice_y_start_offset
        y = choice_y_start + choice_index * (self.choice_height + self.choice_padding)
        x = (self.screen_width - self.choice_width) // 2

        return (x, y, self.choice_width, self.choice_height)

    def is_mouse_over_choice(
        self, mouse_pos: Tuple[int, int], choice_index: int, num_choices: int
    ) -> bool:
        """Check if mouse is over a choice button.

        Args:
            mouse_pos: Mouse position (x, y)
            choice_index: Index of the choice
            num_choices: Total number of choices

        Returns:
            True if mouse is over the choice
        """
        x, y, width, height = self.get_choice_bounds(choice_index, num_choices)
        mouse_x, mouse_y = mouse_pos

        return x <= mouse_x <= x + width and y <= mouse_y <= y + height

    def handle_click(self, event: pygame.event.Event, session: DialogSession) -> bool:
        """Handle a mouse click on the dialog.

        Args:
            event: Pygame mouse button event
            session: The active dialog session

        Returns:
            True if a choice was selected
        """
        if not session or not session.is_active:
            return False

        mouse_pos = event.pos
        choices = session.get_available_choices()

        for i, choice in enumerate(choices):
            if self.is_mouse_over_choice(mouse_pos, i, len(choices)):
                session.make_choice(i)
                return True

        return False

    def render_dialog_box(self):
        """Render the dialog box background and border."""
        x, y, width, height = self.get_dialog_box_bounds()

        # Background
        self.renderer.draw_rect(x, y, width, height, self.bg_color, filled=True)

        # Border
        self.renderer.draw_rect(x, y, width, height, self.border_color, filled=False)

    def render_speaker(self, speaker_name: str):
        """Render the speaker name.

        Args:
            speaker_name: Name of the speaker
        """
        x, y, _, _ = self.get_dialog_box_bounds()

        self.renderer.draw_text(
            speaker_name,
            x + self.dialog_box_padding,
            y + self.dialog_box_padding,
            self.speaker_color,
            font_size=self.speaker_font_size,
        )

    def render_text(self, text: str):
        """Render the dialog text with word wrapping.

        Args:
            text: The text to render
        """
        x, y, width, _ = self.get_dialog_box_bounds()

        text_x = x + self.dialog_box_padding
        text_y = y + self.text_y_offset
        max_width = width - self.dialog_box_padding * 2

        # Scale char_width based on font size (rough approximation: font_size / 2)
        char_width = self.text_font_size // 2

        # Wrap text
        lines = self.wrap_text(text, max_width, char_width=char_width)

        # Render each line
        for i, line in enumerate(lines):
            self.renderer.draw_text(
                line,
                text_x,
                text_y + i * self.text_line_spacing,
                self.text_color,
                font_size=self.text_font_size,
            )

    def render_choices(self, session: DialogSession):
        """Render the dialog choices as buttons.

        Args:
            session: The active dialog session
        """
        choices = session.get_available_choices()

        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()

        for i, choice in enumerate(choices):
            x, y, width, height = self.get_choice_bounds(i, len(choices))

            # Check if hovering
            is_hovering = self.is_mouse_over_choice(mouse_pos, i, len(choices))

            # Button background
            bg_color = self.choice_hover_color if is_hovering else self.choice_bg_color
            self.renderer.draw_rect(x, y, width, height, bg_color, filled=True)
            self.renderer.draw_rect(
                x, y, width, height, self.border_color, filled=False
            )

            # Choice text
            self.renderer.draw_text(
                f"{i+1}. {choice.text}",
                x + self.choice_padding,
                y + self.choice_padding,
                self.text_color,
                font_size=self.choice_font_size,
            )

    def render_session(self, session: DialogSession):
        """Render a complete dialog session.

        This is a convenience method that renders all dialog components.

        Args:
            session: The dialog session to render
        """
        if not session or not session.is_active:
            return

        current_node = session.get_current_node()
        if not current_node:
            return

        # Render dialog box
        self.render_dialog_box()

        # Render speaker
        if current_node.speaker:
            self.render_speaker(current_node.speaker)

        # Render text
        self.render_text(current_node.text)

        # Render choices
        self.render_choices(session)

    def render_with_overlay(self, session: DialogSession, overlay_alpha: int = 180):
        """Render dialog with a semi-transparent overlay over the world.

        This creates a darkened background effect when dialog is active.

        Args:
            session: The dialog session to render
            overlay_alpha: Alpha value for the overlay (0-255)
        """
        # Only works with PygameRenderer
        if hasattr(self.renderer, "screen") and self.renderer.screen:
            # Create semi-transparent overlay
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(overlay_alpha)
            overlay.fill((0, 0, 0))
            self.renderer.screen.blit(overlay, (0, 0))

        # Render dialog on top
        self.render_session(session)

    def configure(
        self,
        dialog_box_height: Optional[int] = None,
        dialog_box_margin: Optional[int] = None,
        choice_height: Optional[int] = None,
        choice_width: Optional[int] = None,
        bg_color: Optional[Color] = None,
        speaker_color: Optional[Color] = None,
        speaker_font_size: Optional[int] = None,
        text_font_size: Optional[int] = None,
        choice_font_size: Optional[int] = None,
        choice_y_start_offset: Optional[int] = None,
        text_y_offset: Optional[int] = None,
        text_line_spacing: Optional[int] = None,
    ):
        """Configure dialog renderer appearance.

        Args:
            dialog_box_height: Height of the dialog box
            dialog_box_margin: Margin from screen edges
            choice_height: Height of choice buttons
            choice_width: Width of choice buttons
            bg_color: Background color
            speaker_color: Speaker name color
        """
        if dialog_box_height is not None:
            self.dialog_box_height = dialog_box_height
        if dialog_box_margin is not None:
            self.dialog_box_margin = dialog_box_margin
        if choice_height is not None:
            self.choice_height = choice_height
        if choice_width is not None:
            self.choice_width = choice_width
        if bg_color is not None:
            self.bg_color = bg_color
        if speaker_color is not None:
            self.speaker_color = speaker_color
        if speaker_font_size is not None:
            self.speaker_font_size = speaker_font_size
        if text_font_size is not None:
            self.text_font_size = text_font_size
        if choice_font_size is not None:
            self.choice_font_size = choice_font_size
        if choice_y_start_offset is not None:
            self.choice_y_start_offset = choice_y_start_offset
        if text_y_offset is not None:
            self.text_y_offset = text_y_offset
        if text_line_spacing is not None:
            self.text_line_spacing = text_line_spacing
