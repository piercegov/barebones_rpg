"""Abstract rendering interface.

This module provides the abstract renderer interface that different
rendering backends can implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, List, Dict
from dataclasses import dataclass


@dataclass
class Color:
    """RGB color representation."""

    r: int
    g: int
    b: int
    a: int = 255

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to tuple (R, G, B, A)."""
        return (self.r, self.g, self.b, self.a)

    def to_rgb(self) -> Tuple[int, int, int]:
        """Convert to RGB tuple."""
        return (self.r, self.g, self.b)


# Predefined colors
class Colors:
    """Common color constants."""

    BLACK = Color(0, 0, 0)
    WHITE = Color(255, 255, 255)
    RED = Color(255, 0, 0)
    GREEN = Color(0, 255, 0)
    BLUE = Color(0, 0, 255)
    YELLOW = Color(255, 255, 0)
    CYAN = Color(0, 255, 255)
    MAGENTA = Color(255, 0, 255)
    GRAY = Color(128, 128, 128)
    DARK_GRAY = Color(64, 64, 64)
    LIGHT_GRAY = Color(192, 192, 192)


class Renderer(ABC):
    """Abstract base class for renderers.

    Different rendering backends (Pygame, terminal, web, etc.) implement this interface.
    """

    def __init__(self, width: int, height: int, title: str = "RPG Game"):
        """Initialize the renderer.

        Args:
            width: Screen width
            height: Screen height
            title: Window title
        """
        self.width = width
        self.height = height
        self.title = title
        self.running = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the rendering system."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the rendering system."""
        pass

    @abstractmethod
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the screen.

        Args:
            color: Background color (default: black)
        """
        pass

    @abstractmethod
    def present(self) -> None:
        """Present/flip the rendered frame to screen."""
        pass

    @abstractmethod
    def draw_rect(
        self, x: int, y: int, width: int, height: int, color: Color, filled: bool = True
    ) -> None:
        """Draw a rectangle.

        Args:
            x: X position
            y: Y position
            width: Rectangle width
            height: Rectangle height
            color: Rectangle color
            filled: Whether to fill the rectangle
        """
        pass

    @abstractmethod
    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: Color = Colors.WHITE,
        font_size: int = 16,
    ) -> None:
        """Draw text.

        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: Text color
            font_size: Font size
        """
        pass

    @abstractmethod
    def draw_circle(
        self, x: int, y: int, radius: int, color: Color, filled: bool = True
    ) -> None:
        """Draw a circle.

        Args:
            x: Center X position
            y: Center Y position
            radius: Circle radius
            color: Circle color
            filled: Whether to fill the circle
        """
        pass

    @abstractmethod
    def draw_sprite(
        self,
        sprite_id: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Draw a sprite/image.

        Args:
            sprite_id: ID/path of sprite
            x: X position
            y: Y position
            width: Sprite width (None = original)
            height: Sprite height (None = original)
        """
        pass

    @abstractmethod
    def handle_events(self) -> List[Any]:
        """Handle input events.

        Returns:
            List of events
        """
        pass

    @abstractmethod
    def get_delta_time(self) -> float:
        """Get time since last frame in seconds.

        Returns:
            Delta time
        """
        pass

    def is_running(self) -> bool:
        """Check if renderer is running.

        Returns:
            True if renderer is active
        """
        return self.running


class UIElement(ABC):
    """Base class for UI elements."""

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize UI element.

        Args:
            x: X position
            y: Y position
            width: Element width
            height: Element height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True

    @abstractmethod
    def render(self, renderer: Renderer) -> None:
        """Render the UI element.

        Args:
            renderer: Renderer to draw with
        """
        pass

    @abstractmethod
    def handle_event(self, event: Any) -> bool:
        """Handle an input event.

        Args:
            event: Input event

        Returns:
            True if event was handled
        """
        pass


class TextBox(UIElement):
    """Simple text box UI element."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        font_size: int = 16,
        text_color: Color = Colors.WHITE,
        bg_color: Color = Colors.BLACK,
    ):
        """Initialize text box.

        Args:
            x: X position
            y: Y position
            width: Box width
            height: Box height
            text: Text to display
            font_size: Font size
            text_color: Text color
            bg_color: Background color
        """
        super().__init__(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.bg_color = bg_color

    def render(self, renderer: Renderer) -> None:
        """Render the text box."""
        if not self.visible:
            return

        # Draw background
        renderer.draw_rect(
            self.x, self.y, self.width, self.height, self.bg_color, filled=True
        )

        # Draw border
        renderer.draw_rect(
            self.x, self.y, self.width, self.height, Colors.WHITE, filled=False
        )

        # Draw text (simple word wrapping would go here)
        renderer.draw_text(
            self.text, self.x + 10, self.y + 10, self.text_color, self.font_size
        )

    def handle_event(self, event: Any) -> bool:
        """Handle event (text boxes don't handle events by default)."""
        return False

    def set_text(self, text: str) -> None:
        """Set the text content.

        Args:
            text: New text
        """
        self.text = text
