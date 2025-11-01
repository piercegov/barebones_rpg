"""Pygame implementation of the renderer.

This provides a basic Pygame-based renderer for the framework.
"""

from typing import List, Optional, Any, Dict
import pygame

from .renderer import Renderer, Color, Colors


class PygameRenderer(Renderer):
    """Pygame-based renderer implementation.

    Example:
        >>> renderer = PygameRenderer(800, 600, "My RPG")
        >>> renderer.initialize()
        >>> renderer.clear()
        >>> renderer.draw_text("Hello World!", 100, 100)
        >>> renderer.present()
    """

    def __init__(self, width: int, height: int, title: str = "RPG Game"):
        """Initialize Pygame renderer.

        Args:
            width: Screen width
            height: Screen height
            title: Window title
        """
        super().__init__(width, height, title)
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.fonts: Dict[int, pygame.font.Font] = {}
        self.sprites: Dict[str, pygame.Surface] = {}

    def initialize(self) -> None:
        """Initialize Pygame and create window."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize default font
        self._get_font(16)

    def shutdown(self) -> None:
        """Shutdown Pygame."""
        pygame.quit()
        self.running = False

    def clear(self, color: Optional[Color] = None) -> None:
        """Clear screen to color.

        Args:
            color: Background color
        """
        if self.screen:
            bg_color = color or Colors.BLACK
            self.screen.fill(bg_color.to_rgb())

    def present(self) -> None:
        """Present the rendered frame."""
        pygame.display.flip()
        if self.clock:
            self.clock.tick(60)  # 60 FPS

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
            filled: Whether to fill
        """
        if self.screen:
            rect = pygame.Rect(x, y, width, height)
            if filled:
                pygame.draw.rect(self.screen, color.to_rgb(), rect)
            else:
                pygame.draw.rect(self.screen, color.to_rgb(), rect, 2)

    def draw_circle(
        self, x: int, y: int, radius: int, color: Color, filled: bool = True
    ) -> None:
        """Draw a circle.

        Args:
            x: X center position
            y: Y center position
            radius: Circle radius
            color: Circle color
            filled: Whether to fill (True) or just outline (False)
        """
        if self.screen:
            if filled:
                pygame.draw.circle(self.screen, color.to_rgb(), (x, y), radius)
            else:
                pygame.draw.circle(self.screen, color.to_rgb(), (x, y), radius, 2)

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
        if self.screen:
            font = self._get_font(font_size)
            text_surface = font.render(text, True, color.to_rgb())
            self.screen.blit(text_surface, (x, y))

    def draw_sprite(
        self,
        sprite_id: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Draw a sprite.

        Args:
            sprite_id: Sprite ID/path
            x: X position
            y: Y position
            width: Scaled width
            height: Scaled height
        """
        if self.screen:
            sprite = self._get_sprite(sprite_id)
            if sprite:
                if width and height:
                    sprite = pygame.transform.scale(sprite, (width, height))
                self.screen.blit(sprite, (x, y))

    def handle_events(self) -> List[Any]:
        """Handle Pygame events.

        Returns:
            List of pygame events
        """
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        return events

    def get_delta_time(self) -> float:
        """Get delta time in seconds.

        Returns:
            Time since last frame
        """
        if self.clock:
            return self.clock.get_time() / 1000.0
        return 0.0

    def _get_font(self, size: int) -> pygame.font.Font:
        """Get or create a font of given size.

        Args:
            size: Font size

        Returns:
            Pygame font
        """
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def _get_sprite(self, sprite_id: str) -> Optional[pygame.Surface]:
        """Load or get a cached sprite.

        Args:
            sprite_id: Sprite path/ID

        Returns:
            Pygame surface or None
        """
        if sprite_id not in self.sprites:
            try:
                self.sprites[sprite_id] = pygame.image.load(sprite_id)
            except (FileNotFoundError, pygame.error):
                # Return a placeholder surface
                surface = pygame.Surface((32, 32))
                surface.fill((255, 0, 255))  # Magenta placeholder
                self.sprites[sprite_id] = surface

        return self.sprites[sprite_id]

    def load_sprite(self, sprite_id: str, path: str) -> bool:
        """Preload a sprite.

        Args:
            sprite_id: ID to reference sprite by
            path: Path to image file

        Returns:
            True if loaded successfully
        """
        try:
            self.sprites[sprite_id] = pygame.image.load(path)
            return True
        except (FileNotFoundError, pygame.error):
            return False


class PygameGameLoop:
    """Game loop using Pygame renderer.

    This integrates the Pygame renderer with the core Game class.

    Example:
        >>> from barebones_rpg.core import Game, GameConfig
        >>> game = Game(GameConfig(title="My RPG"))
        >>> loop = PygameGameLoop(game)
        >>> loop.run()
    """

    def __init__(self, game: Any, renderer: Optional[PygameRenderer] = None):
        """Initialize game loop.

        Args:
            game: Game instance
            renderer: Pygame renderer (creates default if None)
        """
        self.game = game
        self.renderer = renderer or PygameRenderer(
            game.config.screen_width, game.config.screen_height, game.config.title
        )

    def run(self) -> None:
        """Run the game loop."""
        self.renderer.initialize()
        self.game.start()

        while self.renderer.is_running() and self.game.running:
            # Handle events
            events = self.renderer.handle_events()
            for event in events:
                self.game.handle_input(event)

            # Update game logic
            delta = self.renderer.get_delta_time()
            self.game.update(delta)

            # Render
            self.renderer.clear()
            self._render_game()
            self.renderer.present()

        self.renderer.shutdown()

    def _render_game(self) -> None:
        """Render the game state.

        This is a basic implementation that can be overridden.
        """
        # This would render the current game state
        # For now, just draw a simple message
        self.renderer.draw_text(
            f"Game State: {self.game.state.name}", 10, 10, Colors.WHITE, 24
        )

        # Render based on game state
        if hasattr(self.game, "custom_render"):
            self.game.custom_render(self.renderer)
