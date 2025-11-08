"""Tile-based RPG example with click-to-move and turn-based combat.

This example demonstrates:
- Click-based movement with visible movement range
- Action Points (AP) system for movement
- Turn-based combat using the framework's Combat system
- Enemy AI with pathfinding
- Weapon range requirements for attacking
- Dialog system with quests
- Framework tilemap utilities for simplified code
"""

from typing import Optional
import pygame

from barebones_rpg.core.game import Game, GameConfig
from barebones_rpg.core.events import EventType, Event
from barebones_rpg.entities.entity import Character, NPC, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.entities.ai import SimplePathfindingAI
from barebones_rpg.entities.ai_interface import AIContext
from barebones_rpg.world.world import Location
from barebones_rpg.world.tilemap_pathfinding import TilemapPathfinder
from barebones_rpg.world.action_points import APManager
from barebones_rpg.items.item import EquipSlot, create_weapon
from barebones_rpg.combat.combat import Combat
from barebones_rpg.rendering.pygame_renderer import PygameRenderer
from barebones_rpg.rendering.tile_renderer import TileRenderer
from barebones_rpg.rendering.click_to_move import ClickToMoveHandler
from barebones_rpg.rendering.ui_components import UIComponents
from barebones_rpg.dialog.dialog import (
    DialogTree,
    DialogNode,
    DialogChoice,
    DialogSession,
    DialogConditions,
)
from barebones_rpg.dialog.dialog_renderer import DialogRenderer
from barebones_rpg.quests.quest import (
    Quest,
    QuestObjective,
    ObjectiveType,
    QuestManager,
)


# Constants
TILE_SIZE = 64  # Scaled 2x from 32
GRID_WIDTH = 20
GRID_HEIGHT = 15
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

# Action Points
PLAYER_AP = 5
ENEMY_AP = 3


class TileBasedGame:
    """Main game class for the tile-based example."""

    def __init__(self):
        """Initialize the game."""
        # Core game setup
        self.game = Game(
            GameConfig(
                title="Tile-Based RPG Example",
                screen_width=SCREEN_WIDTH,
                screen_height=SCREEN_HEIGHT,
                fps=60,
            )
        )

        # Pygame renderer
        self.renderer = PygameRenderer(
            SCREEN_WIDTH, SCREEN_HEIGHT, "Tile-Based RPG Example"
        )

        # Framework components for tilemaps
        self.location = self._create_world()
        self.pathfinder = TilemapPathfinder(self.location)
        self.ap_manager = APManager(player_ap=PLAYER_AP, enemy_ap=ENEMY_AP)
        self.tile_renderer = TileRenderer(self.renderer, tile_size=TILE_SIZE)
        self.click_handler = ClickToMoveHandler(
            TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, self.pathfinder
        )
        self.ui_components = UIComponents(self.renderer)
        self.dialog_renderer = DialogRenderer(
            self.renderer, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        # Scale dialog renderer dimensions 2x
        self.dialog_renderer.configure(
            dialog_box_height=800,
            dialog_box_margin=40,
            choice_height=80,
            choice_width=1000,
            speaker_font_size=40,
            text_font_size=32,
            choice_font_size=32,
            choice_y_start_offset=360,
            text_y_offset=120,
            text_line_spacing=44,
        )
        # Update internal padding values
        self.dialog_renderer.dialog_box_padding = 40
        self.dialog_renderer.choice_padding = 20

        # AI setup
        self.goblin_ai = SimplePathfindingAI(self.pathfinder)

        # Game state
        self.player: Optional[Character] = None
        self.friendly_npc: Optional[NPC] = None
        self.enemy: Optional[Enemy] = None
        self.player_turn = True

        # Combat
        self.in_combat = False
        self.combat: Optional[Combat] = None
        self.combat_messages: list[str] = []

        # Dialog
        self.in_dialog = False
        self.dialog_session: Optional[DialogSession] = None
        self.dialog_trees: dict[str, DialogTree] = {}

        # Quest
        self.goblin_quest: Optional[Quest] = None

        self._populate_world()
        self._create_quests()
        self._create_dialogs()

        # Subscribe to events
        self.game.events.subscribe(EventType.QUEST_COMPLETED, self._on_quest_completed)
        self.game.events.subscribe(EventType.COMBAT_END, self._on_combat_end)
        self.game.events.subscribe(EventType.DAMAGE_DEALT, self._on_damage_dealt)

        # Start first turn
        self.ap_manager.start_turn(self.player)

    def _create_world(self) -> Location:
        """Create the game world with walls (using framework helpers)."""
        location = Location(name="Test Area", width=GRID_WIDTH, height=GRID_HEIGHT)

        # Use framework helper for border walls
        location.create_border_walls()

        # Use framework helpers for interior walls
        location.create_horizontal_wall(5, 7, 7)
        location.create_vertical_wall(12, 3, 5)

        return location

    def _populate_world(self):
        """Add entities to the world."""
        # Create player with sword
        self.player = Character(
            name="Hero",
            stats=Stats(
                strength=15,
                constitution=12,
                intelligence=10,
                dexterity=14,
                charisma=10,
                base_max_hp=50,
                base_max_mp=20,
                hp=100,
                mp=50,
            ),
            faction="player",
        )
        self.player.init_inventory(max_slots=20)
        self.player.init_equipment()

        # Give player a sword (melee weapon with 1 tile range)
        sword = create_weapon(
            "Iron Sword",
            base_damage=10,
            damage_type="physical",
            range=1,
            value=100,
        )
        self.player.inventory.add_item(sword)
        self.player.equipment.equip(sword)

        self.location.add_entity(self.player, 10, 7)

        # Create friendly NPC
        self.friendly_npc = NPC(
            name="Villager",
            description="A friendly villager who doesn't move much.",
            stats=Stats(
                strength=5,
                constitution=8,
                intelligence=10,
                dexterity=8,
                charisma=12,
                base_max_hp=30,
                hp=50,
            ),
            faction="neutral",
        )
        self.location.add_entity(self.friendly_npc, 5, 5)

        # Create enemy
        self.enemy = Enemy(
            name="Goblin",
            stats=Stats(
                strength=8,
                constitution=6,
                intelligence=5,
                dexterity=12,
                charisma=5,
                base_max_hp=20,
                hp=30,
            ),
            ai=self.goblin_ai,
            faction="enemy",
            exp_reward=20,
            gold_reward=10,
        )
        self.location.add_entity(self.enemy, 15, 10)

    def _create_quests(self):
        """Create quests."""
        self.goblin_quest = Quest(
            name="Kill the Goblin",
            description="The villager needs help dealing with a troublesome goblin.",
            exp_reward=50,
            gold_reward=25,
        )

        # Add to QuestManager (optional, but needed for manager-based lookups)
        QuestManager().add_quest(self.goblin_quest)

        # Use enemy ID for unique target tracking (enables retroactive completion)
        self.goblin_quest.add_objective(
            QuestObjective(
                description="Defeat the Goblin",
                objective_type=ObjectiveType.KILL_ENEMY,
                target=self.enemy.id,
                target_count=1,
            )
        )

        self.goblin_quest.add_objective(
            QuestObjective(
                description="Return to the Villager",
                objective_type=ObjectiveType.TALK_TO_NPC,
                target="Villager",
                target_count=1,
            )
        )

    def _create_dialogs(self):
        """Create dialog trees for NPCs."""
        villager_tree = DialogTree(name="Villager Dialog")

        # Create reusable condition helpers using the framework
        goblin_dead = DialogConditions.entity_not_in_location(self.location, "Goblin")
        goblin_alive = DialogConditions.entity_in_location(self.location, "Goblin")
        quest_not_started = DialogConditions.quest_not_started(self.goblin_quest)
        quest_active = DialogConditions.quest_active(self.goblin_quest)
        quest_completed = DialogConditions.quest_completed(self.goblin_quest)

        # Combined conditions
        quest_ready_to_turn_in = DialogConditions.all_conditions(
            quest_active, goblin_dead
        )

        # Greeting node - changes based on quest status
        greeting = DialogNode(
            id="greeting",
            speaker="Villager",
            text="Hello there, traveler! It's good to see a friendly face in these parts.",
            choices=[
                DialogChoice(
                    text="Do you need any help?",
                    next_node_id="quest_offer",
                    condition=quest_not_started,
                ),
                DialogChoice(
                    text="About that goblin...",
                    next_node_id="quest_in_progress",
                    condition=quest_active,
                ),
                DialogChoice(
                    text="I've dealt with the goblin.",
                    next_node_id="quest_complete",
                    condition=quest_ready_to_turn_in,
                ),
                DialogChoice(
                    text="Thanks again for the reward!",
                    next_node_id="quest_already_complete",
                    condition=quest_completed,
                ),
                DialogChoice(text="How are you doing?", next_node_id="how_are_you"),
                DialogChoice(
                    text="Can you tell me about yourself?", next_node_id="about_you"
                ),
                DialogChoice(text="Goodbye", next_node_id=None),
            ],
        )

        # Quest offer node
        quest_offer = DialogNode(
            id="quest_offer",
            speaker="Villager",
            text="Actually, yes! There's a goblin that's been causing trouble lately. It's somewhere to the east. Could you help deal with it? I can offer some gold and my gratitude in return.",
            choices=[
                DialogChoice(
                    text="I'll take care of it.",
                    next_node_id="quest_accepted_dead",
                    condition=goblin_dead,
                    quest_to_start=self.goblin_quest,
                ),
                DialogChoice(
                    text="I'll take care of it.",
                    next_node_id="quest_accepted",
                    condition=goblin_alive,
                    quest_to_start=self.goblin_quest,
                ),
                DialogChoice(text="Maybe later.", next_node_id=None),
            ],
        )

        # Quest accepted node - normal case
        quest_accepted = DialogNode(
            id="quest_accepted",
            speaker="Villager",
            text="Thank you! The goblin is somewhere to the east. Be careful, and good luck!",
            choices=[DialogChoice(text="I'll be back!", next_node_id=None)],
        )

        # Quest accepted but goblin already dead - special case
        quest_accepted_dead = DialogNode(
            id="quest_accepted_dead",
            speaker="Villager",
            text="Wait... you've already killed it? That's incredible! Thank you so much! Here's your reward.",
            choices=[DialogChoice(text="Happy to help!", next_node_id=None)],
        )

        # Quest in progress node
        quest_in_progress = DialogNode(
            id="quest_in_progress",
            speaker="Villager",
            text="Have you found the goblin yet? It should be somewhere to the east.",
            choices=[
                DialogChoice(text="Still looking.", next_node_id=None),
                DialogChoice(text="I'll find it soon.", next_node_id=None),
            ],
        )

        # Quest complete - turn in (mark turn-in objective complete)
        quest_complete = DialogNode(
            id="quest_complete",
            speaker="Villager",
            text="You have? That's wonderful news! Thank you so much! Here's your reward as promised.",
            choices=[
                DialogChoice(
                    text="Glad I could help!",
                    next_node_id="quest_thank_you",
                    quest_to_update=(
                        self.goblin_quest,
                        ObjectiveType.TALK_TO_NPC,
                        "Villager",
                        1,
                    ),
                )
            ],
        )

        # Thank you node after receiving reward
        quest_thank_you = DialogNode(
            id="quest_thank_you",
            speaker="Villager",
            text="The area is much safer now. Thanks again for your help!",
            choices=[DialogChoice(text="Happy to help!", next_node_id=None)],
        )

        # Quest already completed (subsequent conversations)
        quest_already_complete = DialogNode(
            id="quest_already_complete",
            speaker="Villager",
            text="You've already received your reward, but thank you again! The area is much safer now.",
            choices=[DialogChoice(text="Happy to help!", next_node_id=None)],
        )

        # How are you response - uses condition-based choices for different follow-ups
        how_are_you = DialogNode(
            id="how_are_you",
            speaker="Villager",
            text="I'm doing well, thank you for asking! Just trying to stay safe with that goblin about.",
            choices=[
                DialogChoice(
                    text="Glad you're safe now!",
                    next_node_id=None,
                    condition=goblin_dead,
                ),
                DialogChoice(
                    text="Stay safe!", next_node_id=None, condition=goblin_alive
                ),
            ],
        )

        # About you response
        about_you = DialogNode(
            id="about_you",
            speaker="Villager",
            text="I'm just a simple villager trying to make a living here. Not much to tell, really.",
            choices=[DialogChoice(text="I see. Take care!", next_node_id=None)],
        )

        # Add all nodes to tree
        villager_tree.add_node(greeting)
        villager_tree.add_node(quest_offer)
        villager_tree.add_node(quest_accepted)
        villager_tree.add_node(quest_accepted_dead)
        villager_tree.add_node(quest_in_progress)
        villager_tree.add_node(quest_complete)
        villager_tree.add_node(quest_thank_you)
        villager_tree.add_node(quest_already_complete)
        villager_tree.add_node(how_are_you)
        villager_tree.add_node(about_you)
        villager_tree.set_start_node("greeting")

        # Store dialog tree
        self.dialog_trees["villager"] = villager_tree

    def run(self):
        """Main game loop."""
        self.renderer.initialize()
        self.game.start()

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
                            self._handle_combat_input()
                        elif not self.in_dialog:
                            self._end_turn()

            # Update game
            delta = self.renderer.get_delta_time()
            self.game.update(delta)

            # Render
            self.renderer.clear()
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
        if self.in_combat or self.in_dialog or not self.player_turn or not self.player:
            return

        valid_moves = self.ap_manager.calculate_valid_moves(
            self.player, self.location, self.pathfinder
        )

        self.click_handler.handle_mouse_motion(
            event, valid_moves=valid_moves, current_position=self.player.position
        )

    def _handle_mouse_click(self, event: pygame.event.Event):
        """Handle mouse clicks for movement and interaction."""
        # Handle dialog choices
        if self.in_dialog:
            if self.dialog_session and self.dialog_renderer.handle_click(
                event, self.dialog_session
            ):
                if not self.dialog_session.is_active:
                    self._end_dialog()
            return

        if not self.player_turn or self.in_combat or not self.player:
            return

        tile_pos = self.click_handler.screen_to_tile(event.pos[0], event.pos[1])
        if not tile_pos:
            return

        entity_at_tile = self.location.get_entity_at(tile_pos[0], tile_pos[1])
        valid_moves = self.ap_manager.calculate_valid_moves(
            self.player, self.location, self.pathfinder
        )

        if entity_at_tile and entity_at_tile != self.player:
            if entity_at_tile.faction == "enemy":
                self._try_attack_enemy(entity_at_tile)
            elif entity_at_tile.faction == "neutral":
                self._interact_with_npc(entity_at_tile)
        elif tile_pos in valid_moves:
            self._move_player(tile_pos)

    def _try_attack_enemy(self, enemy: Enemy):
        """Try to attack an enemy (must be in weapon range)."""
        if not self.player:
            return

        distance = self.pathfinder.get_manhattan_distance(
            self.player.position, enemy.position
        )

        weapon = (
            self.player.equipment.get_equipped(EquipSlot.WEAPON)
            if self.player.equipment
            else None
        )
        weapon_range = weapon.range if weapon else 1

        if distance <= weapon_range:
            self._start_combat(self.player, enemy)
        else:
            print(f"Enemy is too far! Need to be within {weapon_range} tile(s).")

    def _interact_with_npc(self, npc: NPC):
        """Interact with a friendly NPC."""
        dialog_tree = self.dialog_trees.get("villager")

        if dialog_tree:
            self.dialog_session = DialogSession(
                dialog_tree,
                game=self.game,
                context={"player": self.player, "location": self.location},
            )
            self.dialog_session.start()
            self.in_dialog = True

    def _end_dialog(self):
        """End the current dialog session."""
        self.in_dialog = False
        self.dialog_session = None

    def _move_player(self, target):
        """Move the player to the target tile."""
        success = self.ap_manager.process_movement(
            self.player, self.location, target, self.pathfinder
        )

        if success:
            remaining = self.ap_manager.get_remaining_ap(self.player)
            print(f"Moved to {target}. AP remaining: {remaining}")

            if remaining <= 0:
                self._end_turn()

    def _end_turn(self):
        """End the current turn."""
        if not self.player_turn:
            return

        print("\n--- Ending Player Turn ---")
        self.player_turn = False

        # Process enemy turns using AI
        self._process_enemy_turns()

        # Start next player turn
        print("\n--- Player Turn Start ---")
        self.player_turn = True
        self.ap_manager.start_turn(self.player)

    def _process_enemy_turns(self):
        """Process all enemy turns using AI."""
        enemies = [e for e in self.location.entities if e.faction == "enemy"]

        for enemy in enemies:
            print(f"\n{enemy.name}'s turn:")

            # Skip if enemy has no AI
            if not enemy.ai:
                print(f"  {enemy.name} has no AI, skipping turn")
                continue

            # Create AI context for the enemy
            context = AIContext(
                entity=enemy,
                nearby_entities=[self.player],
                metadata={"location": self.location},
            )

            # Get AI decision directly from the enemy's AI
            action = enemy.ai.decide_action(context)

            if action and action.get("action") == "attack":
                self._start_combat(enemy, action.get("target"))
                attacked = True
            elif action and action.get("action") == "move":
                # Execute the move
                target_pos = action.get("position")
                if target_pos:
                    if self.location.is_walkable(target_pos[0], target_pos[1]):
                        if (
                            self.location.get_entity_at(target_pos[0], target_pos[1])
                            is None
                        ):
                            self.location.remove_entity(enemy)
                            self.location.add_entity(
                                enemy, target_pos[0], target_pos[1]
                            )
                            enemy.position = target_pos
                            print(f"  {enemy.name} moves to {target_pos}")
                attacked = False
            else:
                attacked = False
            if attacked:
                return  # Combat started, stop processing

    def _start_combat(self, attacker, target):
        """Start combat between attacker and target.

        Args:
            attacker: The entity initiating combat
            target: The entity being attacked
        """
        # Determine which is the enemy (could be initiated by player or enemy)
        if attacker.faction == "enemy":
            enemy = attacker
        else:
            enemy = target

        print(f"\n=== Combat Started: {self.player.name} vs {enemy.name} ===")
        self.in_combat = True
        self.combat_messages = [
            f"Combat: {self.player.name} vs {enemy.name}",
            "",
            "Press SPACE to auto-battle",
        ]

        self.combat = Combat(
            player_group=[self.player], enemy_group=[enemy], events=self.game.events
        )

        self.combat.start()

    def _on_damage_dealt(self, event: Event):
        """Handle damage dealt event."""
        if not event.data:
            return

        source = event.data.get("source")
        target = event.data.get("target")
        damage = event.data.get("damage", 0)

        if source and target:
            msg = f"{source.name} deals {damage} damage to {target.name}!"
            self.combat_messages.append(msg)
            print(msg)

    def _on_quest_completed(self, event: Event):
        """Handle quest completion event to give rewards."""
        if not event.data:
            return

        quest = event.data.get("quest")
        if quest and quest == self.goblin_quest and self.player:
            # Give experience
            if quest.exp_reward > 0:
                self.player.gain_exp(quest.exp_reward, self.game.events)
                print(f"\n✨ Gained {quest.exp_reward} EXP!")

            # Give gold
            if quest.gold_reward > 0 and self.player.inventory:
                self.player.inventory.add_gold(quest.gold_reward)
                print(f"✨ Gained {quest.gold_reward} gold!")

    def _on_combat_end(self, event: Event):
        """Handle combat end event."""
        if not event.data:
            return

        result = event.data.get("result", "UNKNOWN")
        victory = result == "VICTORY"

        if victory:
            msg = "Victory!"
            self.combat_messages.append(msg)
            print(msg)

            # Remove dead enemies from location
            enemies_to_remove = [
                e
                for e in self.location.entities
                if e.faction == "enemy" and e.stats.hp <= 0
            ]
            for enemy in enemies_to_remove:
                self.location.remove_entity(enemy)
        else:
            msg = "Defeat..."
            self.combat_messages.append(msg)
            print(msg)
            self.game.running = False

        self.combat_messages.append("")
        self.combat_messages.append("Press SPACE to continue...")

    def _handle_combat_input(self):
        """Handle input during combat."""
        if not self.combat or not self.in_combat:
            return

        if not self.combat.is_active():
            self.in_combat = False
            self.combat = None
            self.combat_messages = []
            print("\n=== Returning to exploration ===\n")
        else:
            from barebones_rpg.combat.actions import AttackAction

            current_entity = self.combat.get_current_combatant()

            if current_entity and current_entity in self.combat.players.members:
                alive_enemies = self.combat.enemies.get_alive_members()
                if alive_enemies:
                    action = AttackAction()
                    self.combat.execute_action(
                        action, current_entity, [alive_enemies[0]]
                    )

                    from barebones_rpg.combat.combat import CombatState

                    if self.combat.state not in [
                        CombatState.VICTORY,
                        CombatState.DEFEAT,
                        CombatState.FLED,
                    ]:
                        self.combat.end_turn()

    def _render_world(self):
        """Render the world view."""
        valid_moves = (
            self.ap_manager.calculate_valid_moves(
                self.player, self.location, self.pathfinder
            )
            if self.player_turn and self.player
            else set()
        )

        # Use framework's tile renderer
        self.tile_renderer.render_location(
            self.location,
            valid_moves=valid_moves,
            path_preview=self.click_handler.get_path_preview(),
            hover_tile=self.click_handler.get_hover_tile(),
            current_entity_position=self.player.position if self.player else None,
        )

        # Use framework's UI components
        self.ui_components.render_turn_indicator(
            self.player_turn, (20, 20), font_size=40
        )

        self.ui_components.render_resource_bar(
            "AP",
            self.ap_manager.get_remaining_ap(self.player),
            PLAYER_AP,
            (300, 20),
            font_size=40,
        )

        self.ui_components.render_quest_list(
            self.game.quests,
            (20, 100),
            title_font_size=32,
            quest_font_size=28,
            objective_font_size=24,
        )

        instructions = [
            "Click tile to move",
            "Click enemy to attack",
            "Click NPC to talk",
            "SPACE to end turn",
        ]
        self.ui_components.render_instructions(
            instructions, (20, SCREEN_HEIGHT - 150), font_size=24
        )

    def _render_combat(self):
        """Render the combat screen."""
        from barebones_rpg.rendering.renderer import Color, Colors

        self.renderer.clear(Color(20, 20, 30))

        self.renderer.draw_text(
            "=== COMBAT ===", SCREEN_WIDTH // 2 - 160, 100, Colors.RED, font_size=48
        )

        # Use framework's stat panel
        self.ui_components.render_stat_panel(
            self.player,
            (100, 200),
            name_font_size=40,
            stat_font_size=32,
            line_spacing=40,
        )

        if self.combat and self.combat.enemies.members:
            enemy = self.combat.enemies.members[0]
            self.ui_components.render_stat_panel(
                enemy,
                (SCREEN_WIDTH - 300, 200),
                name_font_size=40,
                stat_font_size=32,
                line_spacing=40,
            )

        # Use framework's message log
        self.ui_components.render_message_log(
            self.combat_messages, (100, 400), font_size=28, line_spacing=40
        )

    def _render_dialog(self):
        """Render the dialog screen."""
        # Render world in background
        self._render_world()

        # Use framework's dialog renderer
        self.dialog_renderer.render_with_overlay(self.dialog_session)


def main():
    """Run the tile-based example."""
    print("=== Tile-Based RPG Example ===")
    print("Controls:")
    print("  - Click on tiles to move (within blue highlighted range)")
    print("  - Click on enemies to attack (must be adjacent)")
    print("  - Click on NPCs to talk")
    print("  - SPACE/ENTER to end turn")
    print("  - During combat, SPACE to continue")
    print()

    game = TileBasedGame()
    game.run()

    print("\nThanks for playing!")


if __name__ == "__main__":
    main()
