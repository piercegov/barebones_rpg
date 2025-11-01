"""Turn-based combat system.

This module provides the core combat management system.
"""

from typing import List, Optional, Dict, Any, Callable, Union, TYPE_CHECKING
from enum import Enum, auto
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from .actions import CombatAction, ActionResult, AttackAction
from ..core.events import EventManager, Event, EventType

if TYPE_CHECKING:
    from ..party.party import Party


class CombatState(Enum):
    """States of combat."""

    NOT_STARTED = auto()
    TURN_START = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    TURN_END = auto()
    VICTORY = auto()
    DEFEAT = auto()
    FLED = auto()


class CombatantGroup(BaseModel):
    """A group of combatants (party or enemy group)."""

    name: str = Field(description="Group name")
    members: List[Any] = Field(default_factory=list, description="Group members")

    model_config = {"arbitrary_types_allowed": True}

    def get_alive_members(self) -> List[Any]:
        """Get all living members.

        Returns:
            List of alive members
        """
        return [m for m in self.members if m.is_alive()]

    def is_defeated(self) -> bool:
        """Check if entire group is defeated.

        Returns:
            True if all members are dead
        """
        return len(self.get_alive_members()) == 0

    def add_member(self, member: Any) -> bool:
        """Add a member to the group.

        Args:
            member: Entity to add

        Returns:
            True if member was added successfully
        """
        self.members.append(member)
        return True

    def remove_member(self, member: Any) -> bool:
        """Remove a member from the group.

        Args:
            member: Entity to remove

        Returns:
            True if member was found and removed
        """
        if member in self.members:
            self.members.remove(member)
            return True
        return False


class TurnOrder(BaseModel):
    """Manages turn order based on speed."""

    combatants: List[Any] = Field(default_factory=list, description="All combatants")
    current_index: int = Field(default=0, description="Current turn index")

    model_config = {"arbitrary_types_allowed": True}

    def initialize(self, all_combatants: List[Any]) -> None:
        """Initialize turn order.

        Args:
            all_combatants: All entities in combat
        """
        # Sort by speed (highest first)
        self.combatants = sorted(
            all_combatants, key=lambda c: c.stats.speed, reverse=True
        )
        self.current_index = 0

    def get_current(self) -> Optional[Any]:
        """Get the current combatant.

        Returns:
            Current combatant or None if none available
        """
        alive = self.get_alive_combatants()
        if not alive:
            return None

        # Find next alive combatant
        while self.current_index < len(self.combatants):
            current = self.combatants[self.current_index]
            if current.is_alive():
                return current
            self.current_index += 1

        # Wrapped around, restart
        self.current_index = 0
        return self.get_current()

    def next_turn(self) -> Optional[Any]:
        """Move to next turn.

        Returns:
            Next combatant
        """
        self.current_index += 1
        if self.current_index >= len(self.combatants):
            self.current_index = 0
        return self.get_current()

    def get_alive_combatants(self) -> List[Any]:
        """Get all alive combatants.

        Returns:
            List of alive combatants
        """
        return [c for c in self.combatants if c.is_alive()]


class Combat:
    """Turn-based combat manager.

    Manages combat between two groups (players vs enemies), handles turn order,
    and processes combat actions.

    Example:
        >>> from barebones_rpg.entities import Character, Enemy
        >>> from barebones_rpg.core import EventManager
        >>> from barebones_rpg.party import Party
        >>>
        >>> hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
        >>> goblin = Enemy(name="Goblin", stats=Stats(hp=30, atk=5))
        >>>
        >>> # Using lists (backward compatible)
        >>> combat = Combat(
        ...     player_group=[hero],
        ...     enemy_group=[goblin],
        ...     events=EventManager()
        ... )
        >>>
        >>> # Or using Party objects
        >>> party = Party(name="Heroes", members=[hero])
        >>> enemies = Party(name="Monsters", members=[goblin])
        >>> combat = Combat(
        ...     player_group=party,
        ...     enemy_group=enemies,
        ...     events=EventManager()
        ... )
        >>> combat.start()
        >>> # Combat is now active
    """

    def __init__(
        self,
        player_group: Union[List[Any], "Party"],
        enemy_group: Union[List[Any], "Party"],
        events: Optional[EventManager] = None,
    ):
        """Initialize combat.

        Args:
            player_group: List of player characters or Party object
            enemy_group: List of enemies or Party object
            events: Event manager for publishing combat events
        """
        # Convert Party objects to lists for CombatantGroup
        # This maintains backward compatibility while supporting the new Party system
        player_members = (
            player_group.members if hasattr(player_group, "members") else player_group
        )
        enemy_members = (
            enemy_group.members if hasattr(enemy_group, "members") else enemy_group
        )

        self.players = CombatantGroup(name="Players", members=player_members)
        self.enemies = CombatantGroup(name="Enemies", members=enemy_members)
        self.events = events or EventManager()

        self.state = CombatState.NOT_STARTED
        self.turn_order = TurnOrder()
        self.turn_number = 0

        # Combat state tracking
        self.action_history: List[Dict[str, Any]] = []
        self.dropped_loot: List[Any] = []  # LootDrop objects

        # Callbacks
        self._on_victory: List[Callable] = []
        self._on_defeat: List[Callable] = []
        self._on_flee: List[Callable] = []

    def start(self) -> None:
        """Start combat."""
        all_combatants = self.players.members + self.enemies.members
        self.turn_order.initialize(all_combatants)

        self.state = CombatState.TURN_START
        self.turn_number = 1

        self.events.publish(
            Event(
                EventType.COMBAT_START,
                {
                    "players": self.players.members,
                    "enemies": self.enemies.members,
                },
            )
        )

        self._start_next_turn()

    def _start_next_turn(self) -> None:
        """Start the next turn."""
        # Process status effects for all combatants
        for combatant in self.turn_order.get_alive_combatants():
            if hasattr(combatant, "stats_manager"):
                combatant.stats_manager.process_status_effects()

        current = self.turn_order.get_current()
        if current is None:
            # No one left, shouldn't happen but handle it
            return

        self.events.publish(
            Event(
                EventType.COMBAT_TURN_START,
                {
                    "turn": self.turn_number,
                    "combatant": current,
                },
            )
        )

        # Determine if it's player or enemy turn
        if current in self.players.members:
            self.state = CombatState.PLAYER_TURN
        else:
            self.state = CombatState.ENEMY_TURN
            # Auto-execute enemy turn
            self._execute_enemy_ai(current)

    def execute_action(
        self, action: CombatAction, source: Any, targets: List[Any]
    ) -> ActionResult:
        """Execute a combat action.

        Args:
            action: The action to execute
            source: Entity performing the action
            targets: List of target entities (can be empty for self-targeting actions)

        Returns:
            Result of the action
        """
        # Check if action can be executed
        if not action.can_execute(source, {"combat_state": self}):
            return ActionResult(
                success=False, message=f"{source.name} can't perform {action.name}!"
            )

        # Execute the action
        result = action.execute(source, targets, {"combat_state": self})

        # Record in history
        self.action_history.append(
            {
                "turn": self.turn_number,
                "source": source.id,
                "targets": [t.id for t in targets] if targets else [],
                "action": action.name,
                "result": result,
            }
        )

        # Publish events for each target hit
        if result.targets_hit:
            for target in result.targets_hit:
                self.events.publish(
                    Event(
                        (
                            EventType.ATTACK
                            if action.action_type.name == "ATTACK"
                            else "combat_action"
                        ),
                        {
                            "source": source,
                            "target": target,
                            "action": action,
                            "result": result,
                        },
                    )
                )
        else:
            # Publish event without specific target (e.g., missed attack, failed action)
            self.events.publish(
                Event(
                    (
                        EventType.ATTACK
                        if action.action_type.name == "ATTACK"
                        else "combat_action"
                    ),
                    {
                        "source": source,
                        "target": targets[0] if targets else None,
                        "action": action,
                        "result": result,
                    },
                )
            )

        # Check for deaths and handle loot drops
        for target in result.targets_hit:
            if target.is_dead():
                self.events.publish(
                    Event(EventType.DEATH, {"entity": target, "killer": source})
                )
                self._handle_loot_drops(target)

        # Check if combat should end
        if result.metadata.get("fled"):
            self._end_combat(CombatState.FLED)
        elif self._check_combat_end():
            pass  # _check_combat_end handles ending

        return result

    def end_turn(self) -> None:
        """End the current turn and move to next."""
        current = self.turn_order.get_current()

        self.events.publish(
            Event(
                EventType.COMBAT_TURN_END,
                {"turn": self.turn_number, "combatant": current},
            )
        )

        # Move to next combatant
        next_combatant = self.turn_order.next_turn()

        # Check if we wrapped around (new round)
        if self.turn_order.current_index == 0:
            self.turn_number += 1

        # Start next turn
        self._start_next_turn()

    def _execute_enemy_ai(self, enemy: Any) -> None:
        """Execute AI for an enemy turn.

        Args:
            enemy: Enemy taking turn
        """
        # Simple AI: attack random player
        alive_players = self.players.get_alive_members()
        if not alive_players:
            return

        import random

        target = random.choice(alive_players)

        # Execute basic attack (wrap target in list)
        action = AttackAction()
        result = self.execute_action(action, enemy, [target])

        # Auto-end turn after AI action
        self.end_turn()

    def _check_combat_end(self) -> bool:
        """Check if combat should end.

        Returns:
            True if combat ended
        """
        if self.players.is_defeated():
            self._end_combat(CombatState.DEFEAT)
            return True
        elif self.enemies.is_defeated():
            self._end_combat(CombatState.VICTORY)
            return True
        return False

    def _end_combat(self, end_state: CombatState) -> None:
        """End combat with a specific result.

        Args:
            end_state: How combat ended
        """
        self.state = end_state

        self.events.publish(
            Event(
                EventType.COMBAT_END,
                {
                    "result": end_state.name,
                    "turns": self.turn_number,
                },
            )
        )

        # Call appropriate callbacks
        if end_state == CombatState.VICTORY:
            for callback in self._on_victory:
                callback(self)
        elif end_state == CombatState.DEFEAT:
            for callback in self._on_defeat:
                callback(self)
        elif end_state == CombatState.FLED:
            for callback in self._on_flee:
                callback(self)

    def on_victory(self, callback: Callable) -> None:
        """Register callback for victory.

        Args:
            callback: Function to call on victory
        """
        self._on_victory.append(callback)

    def on_defeat(self, callback: Callable) -> None:
        """Register callback for defeat.

        Args:
            callback: Function to call on defeat
        """
        self._on_defeat.append(callback)

    def on_flee(self, callback: Callable) -> None:
        """Register callback for fleeing.

        Args:
            callback: Function to call when fled
        """
        self._on_flee.append(callback)

    def get_current_combatant(self) -> Optional[Any]:
        """Get the current combatant whose turn it is.

        Returns:
            Current combatant
        """
        return self.turn_order.get_current()

    def is_player_turn(self) -> bool:
        """Check if it's a player's turn.

        Returns:
            True if current turn is a player
        """
        return self.state == CombatState.PLAYER_TURN

    def is_active(self) -> bool:
        """Check if combat is still active.

        Returns:
            True if combat is ongoing
        """
        return self.state not in [
            CombatState.NOT_STARTED,
            CombatState.VICTORY,
            CombatState.DEFEAT,
            CombatState.FLED,
        ]

    def _handle_loot_drops(self, entity: Any) -> None:
        """Handle loot drops from a defeated entity.

        Args:
            entity: The entity that was defeated
        """
        # Check if entity has a loot table
        if not hasattr(entity, "loot_table") or not entity.loot_table:
            return

        # Import here to avoid circular dependency
        from ..items.loot import roll_loot_table

        # Roll for loot
        drops = roll_loot_table(entity.loot_table, source=entity)

        # Store and publish events for each drop
        for drop in drops:
            self.dropped_loot.append(drop)
            self.events.publish(
                Event(
                    EventType.ITEM_DROPPED,
                    {"loot_drop": drop, "item": drop.item, "source": entity},
                )
            )

    def get_dropped_loot(self) -> List[Any]:
        """Get all loot dropped during this combat.

        Returns:
            List of LootDrop objects

        Example:
            >>> combat = Combat(...)
            >>> # ... combat happens ...
            >>> for drop in combat.get_dropped_loot():
            ...     player.inventory.add_item(drop.item)
        """
        return self.dropped_loot
