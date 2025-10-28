"""Base entity system for characters, NPCs, and enemies.

This module provides the base Entity class that all game entities inherit from.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import uuid4
from pydantic import BaseModel, Field

from .stats import Stats, StatsManager
from ..core.events import EventManager, Event, EventType

if TYPE_CHECKING:
    from ..items import Inventory, Equipment


class Entity(BaseModel):
    """Base class for all entities in the game (characters, NPCs, enemies).

    Entities have stats, can participate in combat, and can be extended
    with custom behavior.

    Example:
        >>> hero = Entity(name="Hero", stats=Stats(hp=100, atk=15))
        >>> goblin = Entity(name="Goblin", stats=Stats(hp=30, atk=5))
        >>> hero.stats.hp -= 10  # Take damage
        >>> print(hero.is_alive())
        True
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique entity ID")
    name: str = Field(description="Entity name")
    description: str = Field(default="", description="Entity description")

    # Stats
    stats: Stats = Field(default_factory=Stats, description="Entity stats")

    # Inventory (will be populated by item system)
    inventory_slots: int = Field(default=20, description="Number of inventory slots")
    inventory: Optional[Any] = Field(default=None, description="Inventory instance")
    equipment: Optional[Any] = Field(default=None, description="Equipment instance")
    equipped_items: Dict[str, str] = Field(
        default_factory=dict, description="Equipped items by slot (deprecated, use equipment)"
    )

    # Combat
    faction: str = Field(default="neutral", description="Entity faction (player, enemy, etc.)")
    can_act: bool = Field(default=True, description="Whether entity can take actions")

    # Position (will be used by world system)
    position: tuple[int, int] = Field(default=(0, 0), description="World position (x, y)")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata"
    )

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data):
        super().__init__(**data)
        self._stats_manager = StatsManager(self.stats)
        self._action_callbacks: Dict[str, List] = {}

    @property
    def stats_manager(self) -> StatsManager:
        """Get the stats manager for this entity."""
        return self._stats_manager

    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.stats.is_alive()

    def is_dead(self) -> bool:
        """Check if entity is dead."""
        return self.stats.is_dead()

    def take_damage(self, amount: int, source: Optional["Entity"] = None) -> int:
        """Take damage from an attack.

        Args:
            amount: Base damage amount
            source: Entity that caused the damage

        Returns:
            Actual damage taken after defense calculations
        """
        # Apply defense reduction
        actual_damage = max(1, amount - self.stats.defense)
        self.stats.take_damage(actual_damage)

        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal the entity.

        Args:
            amount: Amount to heal

        Returns:
            Actual amount healed
        """
        return self.stats.restore_hp(amount)

    def restore_mana(self, amount: int) -> int:
        """Restore mana/MP.

        Args:
            amount: Amount to restore

        Returns:
            Actual amount restored
        """
        return self.stats.restore_mp(amount)

    def can_perform_action(self) -> bool:
        """Check if entity can perform an action.

        Returns:
            True if entity can act
        """
        return self.can_act and self.is_alive()

    def init_inventory(self, max_slots: Optional[int] = None) -> Any:
        """Initialize inventory for this entity.

        Args:
            max_slots: Maximum inventory slots (uses inventory_slots if None)

        Returns:
            The created Inventory instance
        """
        from ..items import Inventory
        if self.inventory is None:
            self.inventory = Inventory(max_slots=max_slots or self.inventory_slots)
        return self.inventory

    def init_equipment(self) -> Any:
        """Initialize equipment for this entity.

        Returns:
            The created Equipment instance
        """
        from ..items import Equipment
        if self.equipment is None:
            self.equipment = Equipment()
        return self.equipment

    def register_action(self, action_name: str, callback) -> None:
        """Register a custom action for this entity.

        This allows extending entities with custom behavior.

        Args:
            action_name: Name of the action
            callback: Function to call when action is performed
        """
        if action_name not in self._action_callbacks:
            self._action_callbacks[action_name] = []
        self._action_callbacks[action_name].append(callback)

    def perform_action(self, action_name: str, **kwargs) -> Any:
        """Perform a custom action.

        Args:
            action_name: Name of the action
            **kwargs: Arguments to pass to the action

        Returns:
            Result of the action
        """
        if action_name in self._action_callbacks:
            results = []
            for callback in self._action_callbacks[action_name]:
                results.append(callback(self, **kwargs))
            return results
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for saving.

        Returns:
            Dictionary representation of entity
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create entity from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Entity instance
        """
        return cls(**data)


class Character(Entity):
    """Player character class.

    Extends Entity with character-specific features like experience and leveling.
    """

    faction: str = Field(default="player", description="Character faction")
    character_class: str = Field(default="warrior", description="Character class")
    title: str = Field(default="", description="Character title")

    def gain_exp(self, amount: int, events: Optional[EventManager] = None) -> bool:
        """Gain experience points.

        Args:
            amount: Experience to gain
            events: Event manager to publish level up events

        Returns:
            True if leveled up
        """
        self.stats.exp += amount
        leveled_up = False

        # Check for level up
        while self.stats.exp >= self.stats.exp_to_next:
            self.stats.exp -= self.stats.exp_to_next
            self.level_up()
            leveled_up = True

            if events:
                events.publish(Event(EventType.LEVEL_UP, {"entity": self}))

        return leveled_up

    def level_up(self) -> None:
        """Level up the character.

        This can be overridden to customize stat growth.
        """
        self.stats.level += 1
        self.stats.exp_to_next = int(self.stats.exp_to_next * 1.5)

        # Basic stat increases (can be customized)
        self.stats.max_hp += 10
        self.stats.hp = self.stats.max_hp
        self.stats.max_mp += 5
        self.stats.mp = self.stats.max_mp
        self.stats.atk += 2
        self.stats.defense += 1
        self.stats.speed += 1


class NPC(Entity):
    """Non-player character class.

    NPCs can have dialog, quests, and custom behavior.
    """

    faction: str = Field(default="neutral", description="NPC faction")
    dialog_tree_id: Optional[str] = Field(default=None, description="ID of dialog tree")
    quest_ids: List[str] = Field(default_factory=list, description="Quest IDs this NPC offers")
    is_merchant: bool = Field(default=False, description="Whether NPC is a merchant")
    merchant_inventory: List[str] = Field(
        default_factory=list, description="Items for sale"
    )


class Enemy(Entity):
    """Enemy character class.

    Enemies have AI behavior and drop items/exp when defeated.
    """

    faction: str = Field(default="enemy", description="Enemy faction")
    ai_type: str = Field(default="aggressive", description="AI behavior type")
    exp_reward: int = Field(default=10, description="Experience reward on defeat")
    gold_reward: int = Field(default=5, description="Gold reward on defeat")
    loot_table: List[str] = Field(default_factory=list, description="Possible item drops")
    aggro_range: int = Field(default=5, description="Range at which enemy attacks")
