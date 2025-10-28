"""Tile-based RPG example with click-to-move and turn-based combat.

This example demonstrates:
- Click-based movement with visible movement range
- Action Points (AP) system for movement
- Turn-based combat using the framework's Combat system
- Enemy AI with pathfinding
- Weapon range requirements for attacking
"""

from typing import Optional, Set, Tuple, List, Dict
from collections import deque
import pygame

from barebones_rpg.core.game import Game, GameConfig, GameState
from barebones_rpg.core.events import EventManager, Event, EventType
from barebones_rpg.entities.entity import Character, NPC, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.world.world import Location, Tile
from barebones_rpg.items.item import Item, ItemType, EquipSlot, create_weapon
from barebones_rpg.combat.combat import Combat
from barebones_rpg.rendering.pygame_renderer import PygameRenderer
from barebones_rpg.rendering.renderer import Colors, Color
from barebones_rpg.dialog.dialog import DialogTree, DialogNode, DialogChoice, DialogSession


# Constants
TILE_SIZE = 32
GRID_WIDTH = 20
GRID_HEIGHT = 15
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

# Action Points
PLAYER_AP = 5
ENEMY_AP = 3
NPC_AP = 0


class TileBasedGame:
    """Main game class for the tile-based example."""

    def __init__(self):
        """Initialize the game."""
        self.game = Game(GameConfig(
            title="Tile-Based RPG Example",
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            fps=60
        ))

        self.renderer = PygameRenderer(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "Tile-Based RPG Example"
        )

        # Game state
        self.location = self._create_world()
        self.player: Optional[Character] = None
        self.friendly_npc: Optional[NPC] = None
        self.enemy: Optional[Enemy] = None

        # Turn management
        self.player_turn = True
        self.current_ap = PLAYER_AP

        # Movement
        self.valid_moves: Set[Tuple[int, int]] = set()
        self.path_preview: List[Tuple[int, int]] = []
        self.hover_tile: Optional[Tuple[int, int]] = None

        # Combat
        self.in_combat = False
        self.combat: Optional[Combat] = None
        self.combat_messages: List[str] = []

        # Dialog
        self.in_dialog = False
        self.dialog_session: Optional[DialogSession] = None
        self.dialog_trees: Dict[str, DialogTree] = {}

        self._populate_world()
        self._create_dialogs()

    def _create_world(self) -> Location:
        """Create the game world with walls."""
        location = Location(
            name="Test Area",
            width=GRID_WIDTH,
            height=GRID_HEIGHT
        )

        # Add border walls
        for x in range(GRID_WIDTH):
            location.set_tile(x, 0, Tile(x=x, y=0, tile_type="wall", walkable=False))
            location.set_tile(x, GRID_HEIGHT - 1,
                            Tile(x=x, y=GRID_HEIGHT - 1, tile_type="wall", walkable=False))

        for y in range(GRID_HEIGHT):
            location.set_tile(0, y, Tile(x=0, y=y, tile_type="wall", walkable=False))
            location.set_tile(GRID_WIDTH - 1, y,
                            Tile(x=GRID_WIDTH - 1, y=y, tile_type="wall", walkable=False))

        # Add some interior walls
        for x in range(5, 8):
            location.set_tile(x, 7, Tile(x=x, y=7, tile_type="wall", walkable=False))

        for y in range(3, 6):
            location.set_tile(12, y, Tile(x=12, y=y, tile_type="wall", walkable=False))

        return location

    def _populate_world(self):
        """Add entities to the world."""
        # Create player with sword
        self.player = Character(
            name="Hero",
            stats=Stats(hp=100, max_hp=100, atk=15, defense=5, speed=12, mp=50, max_mp=50),
            faction="player"
        )
        self.player.init_inventory(max_slots=20)
        self.player.init_equipment()

        # Give player a sword (melee weapon with 1 tile range)
        sword = create_weapon("Iron Sword", atk=10, value=100, metadata={"range": 1})
        self.player.inventory.add_item(sword)
        self.player.equipment.equip(sword)

        self.location.add_entity(self.player, 10, 7)

        # Create friendly NPC
        self.friendly_npc = NPC(
            name="Villager",
            description="A friendly villager who doesn't move much.",
            stats=Stats(hp=50, max_hp=50, atk=0, defense=0, speed=5),
            faction="neutral"
        )
        self.location.add_entity(self.friendly_npc, 5, 5)

        # Create enemy
        self.enemy = Enemy(
            name="Goblin",
            stats=Stats(hp=30, max_hp=30, atk=8, defense=2, speed=10),
            faction="enemy",
            exp_reward=20,
            gold_reward=10
        )
        self.location.add_entity(self.enemy, 15, 10)

    def _create_dialogs(self):
        """Create dialog trees for NPCs."""
        # Villager dialog tree
        villager_tree = DialogTree(name="Villager Dialog")

        # Greeting node
        greeting = DialogNode(
            id="greeting",
            speaker="Villager",
            text="Hello there, traveler! It's good to see a friendly face in these parts.",
            choices=[
                DialogChoice(text="How are you doing?", next_node_id="how_are_you"),
                DialogChoice(text="What's happening around here?", next_node_id="whats_happening"),
                DialogChoice(text="Can you tell me about yourself?", next_node_id="about_you"),
                DialogChoice(text="Goodbye", next_node_id=None)
            ]
        )

        # How are you response
        how_are_you = DialogNode(
            id="how_are_you",
            speaker="Villager",
            text="I'm doing well, thank you for asking! Just trying to stay safe with those goblins about.",
            choices=[
                DialogChoice(text="Tell me more", next_node_id="whats_happening"),
                DialogChoice(text="Take care!", next_node_id=None)
            ]
        )

        # What's happening response
        whats_happening = DialogNode(
            id="whats_happening",
            speaker="Villager",
            text="There's a goblin that's been causing trouble lately. Be careful if you see it!",
            choices=[
                DialogChoice(text="I'll deal with it", next_node_id="deal_with_it"),
                DialogChoice(text="Thanks for the warning", next_node_id=None)
            ]
        )

        # Deal with it response
        deal_with_it = DialogNode(
            id="deal_with_it",
            speaker="Villager",
            text="You're brave! The goblin is somewhere to the east. Good luck, and thank you!",
            choices=[
                DialogChoice(text="I'll be back", next_node_id=None),
                DialogChoice(text="Anything else I should know?", next_node_id="about_you")
            ]
        )

        # About you response
        about_you = DialogNode(
            id="about_you",
            speaker="Villager",
            text="I'm just a simple villager trying to make a living here. Not much to tell, really.",
            choices=[
                DialogChoice(text="What about the goblin?", next_node_id="whats_happening"),
                DialogChoice(text="I see. Take care!", next_node_id=None)
            ]
        )

        # Add all nodes to tree
        villager_tree.add_node(greeting)
        villager_tree.add_node(how_are_you)
        villager_tree.add_node(whats_happening)
        villager_tree.add_node(deal_with_it)
        villager_tree.add_node(about_you)
        villager_tree.set_start_node("greeting")

        # Store dialog tree
        self.dialog_trees["villager"] = villager_tree

    def run(self):
        """Main game loop."""
        self.renderer.initialize()
        self.game.start()

        # Calculate initial valid moves
        self._calculate_valid_moves()

        while self.renderer.is_running() and self.game.running:
            events = self.renderer.handle_events()

            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_click(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if self.in_combat:
                            self._handle_combat_input(event)
                        elif self.in_dialog:
                            pass  # Dialog uses mouse clicks for choices
                        else:
                            self._end_turn()

            # Update game
            delta = self.renderer.get_delta_time()
            self.game.update(delta)

            # Render
            self.renderer.clear(Colors.BLACK)
            if self.in_combat:
                self._render_combat()
            elif self.in_dialog:
                self._render_dialog()
            else:
                self._render_world()
            self.renderer.present()

        self.renderer.shutdown()

    def _handle_mouse_motion(self, event: pygame.event.Event):
        """Handle mouse movement to show hover effects."""
        if self.in_combat or self.in_dialog:
            return

        mouse_x, mouse_y = event.pos
        grid_x = mouse_x // TILE_SIZE
        grid_y = mouse_y // TILE_SIZE

        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            self.hover_tile = (grid_x, grid_y)

            # Calculate path preview if hovering over valid tile
            if (grid_x, grid_y) in self.valid_moves and self.player_turn:
                self.path_preview = self._find_path(self.player.position, (grid_x, grid_y))
            else:
                self.path_preview = []
        else:
            self.hover_tile = None
            self.path_preview = []

    def _handle_mouse_click(self, event: pygame.event.Event):
        """Handle mouse clicks for movement and interaction."""
        # Handle dialog choices
        if self.in_dialog:
            self._handle_dialog_click(event)
            return

        if not self.player_turn or self.in_combat:
            return

        mouse_x, mouse_y = event.pos
        grid_x = mouse_x // TILE_SIZE
        grid_y = mouse_y // TILE_SIZE

        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            clicked_tile = (grid_x, grid_y)

            # Check if clicking on an entity
            entity_at_tile = self.location.get_entity_at(grid_x, grid_y)

            if entity_at_tile and entity_at_tile != self.player:
                # Clicked on an entity
                if entity_at_tile.faction == "enemy":
                    self._try_attack_enemy(entity_at_tile)
                elif entity_at_tile.faction == "neutral":
                    self._interact_with_npc(entity_at_tile)
            elif clicked_tile in self.valid_moves:
                # Move to clicked tile
                self._move_player(clicked_tile)

    def _try_attack_enemy(self, enemy: Enemy):
        """Try to attack an enemy (must be in weapon range)."""
        px, py = self.player.position
        ex, ey = enemy.position

        # Calculate distance (Manhattan distance)
        distance = abs(px - ex) + abs(py - ey)

        # Get weapon range from metadata
        weapon = self.player.equipment.get_equipped(EquipSlot.WEAPON)
        weapon_range = weapon.metadata.get('range', 1) if weapon else 1

        if distance <= weapon_range:
            # In range - initiate combat!
            self._start_combat(enemy)
        else:
            print(f"Enemy is too far! Need to be within {weapon_range} tile(s).")

    def _interact_with_npc(self, npc: NPC):
        """Interact with a friendly NPC."""
        print(f"Talking to {npc.name}...")

        # Get dialog tree for this NPC (using simple lookup)
        dialog_tree = self.dialog_trees.get("villager")

        if dialog_tree:
            self.dialog_session = DialogSession(dialog_tree, context={"player": self.player})
            self.dialog_session.start()
            self.in_dialog = True
        else:
            print(f"{npc.name}: {npc.description}")

    def _handle_dialog_click(self, event: pygame.event.Event):
        """Handle mouse clicks during dialog."""
        if not self.dialog_session or not self.dialog_session.is_active:
            return

        mouse_x, mouse_y = event.pos

        # Calculate choice button bounds
        choices = self.dialog_session.get_available_choices()
        choice_y_start = 300
        choice_height = 40
        choice_padding = 10

        for i, choice in enumerate(choices):
            y = choice_y_start + i * (choice_height + choice_padding)
            # Choice buttons are centered and 500px wide
            x = (SCREEN_WIDTH - 500) // 2

            if x <= mouse_x <= x + 500 and y <= mouse_y <= y + choice_height:
                # Clicked on choice i
                print(f"Selected: {choice.text}")
                next_node = self.dialog_session.make_choice(i)

                # Check if dialog ended
                if not self.dialog_session.is_active:
                    self._end_dialog()
                break

    def _end_dialog(self):
        """End the current dialog session."""
        print("Dialog ended")
        self.in_dialog = False
        self.dialog_session = None

    def _move_player(self, target: Tuple[int, int]):
        """Move the player to the target tile."""
        path = self._find_path(self.player.position, target)

        if not path:
            return

        # Calculate AP cost (excluding starting position)
        ap_cost = len(path) - 1

        if ap_cost <= self.current_ap:
            # Move the player
            old_pos = self.player.position
            self.location.remove_entity(self.player)
            self.location.add_entity(self.player, target[0], target[1])
            self.player.position = target

            # Consume AP
            self.current_ap -= ap_cost
            print(f"Moved from {old_pos} to {target}. AP remaining: {self.current_ap}")

            # Recalculate valid moves
            self._calculate_valid_moves()

            # Auto end turn if no AP left
            if self.current_ap <= 0:
                self._end_turn()

    def _end_turn(self):
        """End the current turn."""
        if not self.player_turn:
            return

        print("\n--- Ending Player Turn ---")
        self.player_turn = False
        self.valid_moves.clear()

        # Process enemy turns
        self._process_enemy_turns()

        # Start next player turn
        print("\n--- Player Turn Start ---")
        self.player_turn = True
        self.current_ap = PLAYER_AP
        self._calculate_valid_moves()

    def _process_enemy_turns(self):
        """Process all enemy turns."""
        enemies = [e for e in self.location.entities if e.faction == "enemy"]

        for enemy in enemies:
            print(f"\n{enemy.name}'s turn:")
            self._process_enemy_ai(enemy, ENEMY_AP)

    def _process_enemy_ai(self, enemy: Enemy, ap: int):
        """Process a single enemy's AI turn."""
        px, py = self.player.position
        ex, ey = enemy.position

        # Check if adjacent to player
        distance = abs(px - ex) + abs(py - ey)

        if distance == 1:
            # Adjacent - attack!
            print(f"{enemy.name} attacks {self.player.name}!")
            self._start_combat(enemy)
            return

        # Move toward player
        moves_made = 0
        while moves_made < ap:
            # Calculate path to player
            path = self._find_path(enemy.position, self.player.position)

            if not path or len(path) <= 1:
                break

            # Move one step along path
            next_pos = path[1]  # path[0] is current position

            # Check if tile is walkable and not occupied
            if self.location.is_walkable(next_pos[0], next_pos[1]):
                entity_at_pos = self.location.get_entity_at(next_pos[0], next_pos[1])

                if entity_at_pos is None:
                    # Move enemy
                    self.location.remove_entity(enemy)
                    self.location.add_entity(enemy, next_pos[0], next_pos[1])
                    enemy.position = next_pos
                    moves_made += 1
                    print(f"{enemy.name} moves to {next_pos}")

                    # Check if now adjacent to player
                    new_distance = abs(px - next_pos[0]) + abs(py - next_pos[1])
                    if new_distance == 1:
                        # Adjacent - attack!
                        print(f"{enemy.name} attacks {self.player.name}!")
                        self._start_combat(enemy)
                        return
                else:
                    break
            else:
                break

    def _calculate_valid_moves(self):
        """Calculate all valid moves within AP range using flood fill."""
        self.valid_moves.clear()

        if not self.player_turn or self.current_ap <= 0:
            return

        # Flood fill from player position
        start = self.player.position
        visited = {start: 0}  # position -> cost to reach
        queue = deque([(start, 0)])

        while queue:
            pos, cost = queue.popleft()

            # Check all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)
                new_cost = cost + 1

                # Check if within AP range
                if new_cost > self.current_ap:
                    continue

                # Check if already visited with lower cost
                if new_pos in visited and visited[new_pos] <= new_cost:
                    continue

                # Check if walkable
                if not self.location.is_walkable(new_pos[0], new_pos[1]):
                    continue

                # Check if occupied by entity (can still highlight, just can't move there)
                entity = self.location.get_entity_at(new_pos[0], new_pos[1])

                visited[new_pos] = new_cost
                self.valid_moves.add(new_pos)

                # Only continue flooding if tile is not occupied
                if entity is None:
                    queue.append((new_pos, new_cost))

    def _find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find shortest path from start to goal using BFS."""
        if start == goal:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            pos, path = queue.popleft()

            # Check all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (pos[0] + dx, pos[1] + dy)

                if new_pos in visited:
                    continue

                if not self.location.is_walkable(new_pos[0], new_pos[1]):
                    continue

                # Allow pathing through goal even if occupied
                entity = self.location.get_entity_at(new_pos[0], new_pos[1])
                if entity is not None and new_pos != goal:
                    continue

                new_path = path + [new_pos]

                if new_pos == goal:
                    return new_path

                visited.add(new_pos)
                queue.append((new_pos, new_path))

        return []  # No path found

    def _start_combat(self, enemy: Enemy):
        """Start combat with an enemy."""
        print(f"\n=== Combat Started: {self.player.name} vs {enemy.name} ===")
        self.in_combat = True
        self.combat_messages = [
            f"Combat: {self.player.name} vs {enemy.name}",
            "",
            "Press SPACE to auto-battle"
        ]

        # Create combat instance
        self.combat = Combat(
            player_group=[self.player],
            enemy_group=[enemy],
            events=self.game.events
        )

        # Subscribe to combat events
        self.game.events.subscribe(EventType.COMBAT_END, self._on_combat_end)
        self.game.events.subscribe(EventType.DAMAGE_DEALT, self._on_damage_dealt)

        self.combat.start()

    def _on_damage_dealt(self, event: Event):
        """Handle damage dealt event."""
        source = event.data.get('source')
        target = event.data.get('target')
        damage = event.data.get('damage', 0)

        msg = f"{source.name} deals {damage} damage to {target.name}!"
        self.combat_messages.append(msg)
        print(msg)

    def _on_combat_end(self, event: Event):
        """Handle combat end event."""
        result = event.data.get('result', 'UNKNOWN')
        victory = result == 'VICTORY'

        if victory:
            msg = "Victory!"
            self.combat_messages.append(msg)
            print(msg)

            # Remove dead enemies from location
            enemies_to_remove = [e for e in self.location.entities
                               if e.faction == "enemy" and e.stats.hp <= 0]
            for enemy in enemies_to_remove:
                self.location.remove_entity(enemy)
        else:
            msg = "Defeat..."
            self.combat_messages.append(msg)
            print(msg)
            self.game.running = False

        # Add prompt to continue
        self.combat_messages.append("")
        self.combat_messages.append("Press SPACE to continue...")

    def _handle_combat_input(self, event: pygame.event.Event):
        """Handle input during combat."""
        if not self.combat or not self.in_combat:
            return

        if event.key == pygame.K_SPACE:
            if not self.combat.is_active():
                # Combat is over, return to world
                self.in_combat = False
                self.combat = None
                self.combat_messages = []
                print("\n=== Returning to exploration ===\n")
            else:
                # Execute combat rounds
                self._execute_combat_round()

    def _execute_combat_round(self):
        """Execute one round of combat."""
        if not self.combat or not self.combat.is_active():
            return

        # Simple auto-battle: just process next turn
        from barebones_rpg.combat.actions import AttackAction

        current_entity = self.combat.get_current_combatant()

        if not current_entity:
            return

        if current_entity in self.combat.players.members:
            # Player attacks first alive enemy
            alive_enemies = self.combat.enemies.get_alive_members()
            if alive_enemies:
                target = alive_enemies[0]
                action = AttackAction()
                self.combat.execute_action(action, current_entity, target)

                # Only end turn if combat is still active (action didn't end combat)
                from barebones_rpg.combat.combat import CombatState
                if self.combat.state not in [CombatState.VICTORY, CombatState.DEFEAT, CombatState.FLED]:
                    self.combat.end_turn()
        else:
            # Enemy turn - the AI already executed when the turn started
            # The enemy AI in Combat class already called end_turn()
            # So this turn should already be done, just return
            pass

    def _render_world(self):
        """Render the world view."""
        # Draw tiles
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                tile = self.location.get_tile(x, y)
                screen_x = x * TILE_SIZE
                screen_y = y * TILE_SIZE

                # Tile background
                if tile.walkable:
                    color = Colors.DARK_GRAY
                else:
                    color = Color(40, 40, 40)  # Darker for walls

                self.renderer.draw_rect(
                    screen_x, screen_y, TILE_SIZE, TILE_SIZE, color, filled=True
                )

                # Draw grid lines
                self.renderer.draw_rect(
                    screen_x, screen_y, TILE_SIZE, TILE_SIZE,
                    Color(60, 60, 60), filled=False
                )

        # Highlight valid moves
        if self.player_turn:
            for pos in self.valid_moves:
                if pos != self.player.position:
                    screen_x = pos[0] * TILE_SIZE
                    screen_y = pos[1] * TILE_SIZE
                    # Semi-transparent highlight
                    self.renderer.draw_rect(
                        screen_x + 2, screen_y + 2,
                        TILE_SIZE - 4, TILE_SIZE - 4,
                        Color(100, 100, 255), filled=True
                    )

        # Draw path preview
        for i, pos in enumerate(self.path_preview):
            if i > 0:  # Skip starting position
                screen_x = pos[0] * TILE_SIZE
                screen_y = pos[1] * TILE_SIZE
                self.renderer.draw_rect(
                    screen_x + 4, screen_y + 4,
                    TILE_SIZE - 8, TILE_SIZE - 8,
                    Color(200, 200, 255), filled=True
                )

        # Draw hover highlight
        if self.hover_tile:
            hx, hy = self.hover_tile
            screen_x = hx * TILE_SIZE
            screen_y = hy * TILE_SIZE
            self.renderer.draw_rect(
                screen_x, screen_y, TILE_SIZE, TILE_SIZE,
                Colors.YELLOW, filled=False
            )

        # Draw entities
        for entity in self.location.entities:
            x, y = entity.position
            screen_x = x * TILE_SIZE + TILE_SIZE // 2
            screen_y = y * TILE_SIZE + TILE_SIZE // 2
            radius = TILE_SIZE // 3

            # Choose color based on faction
            if entity.faction == "player":
                color = Colors.BLUE
            elif entity.faction == "enemy":
                color = Colors.RED
            else:
                color = Colors.GREEN

            # Draw circle
            self.renderer.draw_circle(screen_x, screen_y, radius, color)

            # Draw name above entity
            name_width = len(entity.name) * 6
            self.renderer.draw_text(
                entity.name,
                screen_x - name_width // 2,
                screen_y - TILE_SIZE // 2 - 10,
                Colors.WHITE,
                font_size=14
            )

            # Draw HP bar
            hp_percent = entity.stats.hp / entity.stats.max_hp
            bar_width = TILE_SIZE - 4
            bar_height = 4
            bar_x = x * TILE_SIZE + 2
            bar_y = y * TILE_SIZE + TILE_SIZE - 6

            # Background
            self.renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, Colors.RED, filled=True)
            # HP
            self.renderer.draw_rect(
                bar_x, bar_y, int(bar_width * hp_percent), bar_height,
                Colors.GREEN, filled=True
            )

        # Draw UI
        self._render_ui()

    def _render_ui(self):
        """Render UI elements."""
        # Turn indicator
        turn_text = "YOUR TURN" if self.player_turn else "ENEMY TURN"
        turn_color = Colors.GREEN if self.player_turn else Colors.RED
        self.renderer.draw_text(turn_text, 10, 10, turn_color, font_size=20)

        # AP counter
        ap_text = f"AP: {self.current_ap}/{PLAYER_AP}"
        self.renderer.draw_text(ap_text, 150, 10, Colors.WHITE, font_size=20)

        # Instructions
        instructions = [
            "Click tile to move",
            "Click enemy to attack (must be adjacent)",
            "SPACE to end turn"
        ]
        for i, text in enumerate(instructions):
            self.renderer.draw_text(
                text, 10, SCREEN_HEIGHT - 60 + i * 15,
                Colors.LIGHT_GRAY, font_size=12
            )

    def _render_combat(self):
        """Render the combat screen."""
        # Dark background
        self.renderer.clear(Color(20, 20, 30))

        # Title
        self.renderer.draw_text(
            "=== COMBAT ===",
            SCREEN_WIDTH // 2 - 80,
            50,
            Colors.RED,
            font_size=24
        )

        # Player stats
        y_offset = 100
        self.renderer.draw_text(
            f"{self.player.name}",
            50, y_offset,
            Colors.BLUE, font_size=20
        )
        self.renderer.draw_text(
            f"HP: {self.player.stats.hp}/{self.player.stats.max_hp}",
            50, y_offset + 25,
            Colors.WHITE, font_size=16
        )
        self.renderer.draw_text(
            f"ATK: {self.player.stats.atk}",
            50, y_offset + 45,
            Colors.WHITE, font_size=16
        )

        # Enemy stats (if combat active)
        if self.combat and self.combat.enemies.members:
            enemy = self.combat.enemies.members[0]
            self.renderer.draw_text(
                f"{enemy.name}",
                SCREEN_WIDTH - 150, y_offset,
                Colors.RED, font_size=20
            )
            self.renderer.draw_text(
                f"HP: {enemy.stats.hp}/{enemy.stats.max_hp}",
                SCREEN_WIDTH - 150, y_offset + 25,
                Colors.WHITE, font_size=16
            )
            self.renderer.draw_text(
                f"ATK: {enemy.stats.atk}",
                SCREEN_WIDTH - 150, y_offset + 45,
                Colors.WHITE, font_size=16
            )

        # Combat log
        log_y = 200
        max_messages = 15
        visible_messages = self.combat_messages[-max_messages:]

        for i, msg in enumerate(visible_messages):
            self.renderer.draw_text(
                msg,
                50,
                log_y + i * 20,
                Colors.WHITE,
                font_size=14
            )

    def _render_dialog(self):
        """Render the dialog screen."""
        # Semi-transparent overlay over world
        self._render_world()

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        if self.renderer.screen:
            self.renderer.screen.blit(overlay, (0, 0))

        if not self.dialog_session or not self.dialog_session.is_active:
            return

        current_node = self.dialog_session.get_current_node()
        if not current_node:
            return

        # Dialog box background
        dialog_box_height = 400
        dialog_box_y = SCREEN_HEIGHT - dialog_box_height - 20
        self.renderer.draw_rect(
            20, dialog_box_y, SCREEN_WIDTH - 40, dialog_box_height,
            Color(30, 30, 40), filled=True
        )
        self.renderer.draw_rect(
            20, dialog_box_y, SCREEN_WIDTH - 40, dialog_box_height,
            Colors.WHITE, filled=False
        )

        # Speaker name
        if current_node.speaker:
            self.renderer.draw_text(
                current_node.speaker,
                40, dialog_box_y + 20,
                Colors.YELLOW, font_size=20
            )

        # Dialog text (word wrap)
        text_y = dialog_box_y + 60
        text_x = 40
        max_width = SCREEN_WIDTH - 100

        # Simple word wrapping
        words = current_node.text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = len(word) * 8  # Approximate width
            if current_width + word_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width + 8  # Add space width

        if current_line:
            lines.append(" ".join(current_line))

        for i, line in enumerate(lines):
            self.renderer.draw_text(
                line,
                text_x, text_y + i * 22,
                Colors.WHITE, font_size=16
            )

        # Choices
        choices = self.dialog_session.get_available_choices()
        choice_y_start = dialog_box_y + 180
        choice_height = 40
        choice_padding = 10

        for i, choice in enumerate(choices):
            y = choice_y_start + i * (choice_height + choice_padding)
            x = (SCREEN_WIDTH - 500) // 2

            # Get mouse position for hover effect
            mouse_x, mouse_y = pygame.mouse.get_pos()
            is_hovering = x <= mouse_x <= x + 500 and y <= mouse_y <= y + choice_height

            # Choice button background
            button_color = Color(80, 80, 120) if is_hovering else Color(50, 50, 70)
            self.renderer.draw_rect(x, y, 500, choice_height, button_color, filled=True)
            self.renderer.draw_rect(x, y, 500, choice_height, Colors.WHITE, filled=False)

            # Choice text
            self.renderer.draw_text(
                f"{i+1}. {choice.text}",
                x + 10, y + 12,
                Colors.WHITE, font_size=16
            )


def main():
    """Run the tile-based example."""
    print("=== Tile-Based RPG Example ===")
    print("Controls:")
    print("  - Click on tiles to move (within blue highlighted range)")
    print("  - Click on enemies to attack (must be adjacent)")
    print("  - SPACE/ENTER to end turn")
    print("  - During combat, SPACE to continue")
    print()

    game = TileBasedGame()
    game.run()

    print("\nThanks for playing!")


if __name__ == "__main__":
    main()
