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
    from .ai_interface import AIInterface
else:
    AIInterface = Any  # Runtime fallback to avoid circular imports


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
    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique entity ID"
    )
    name: str = Field(description="Entity name")
    description: str = Field(default="", description="Entity description")

    # Stats
    stats: Stats = Field(default_factory=Stats, description="Entity stats")

    # Inventory (will be populated by item system)
    inventory_slots: int = Field(default=20, description="Number of inventory slots")
    inventory: Optional[Any] = Field(default=None, description="Inventory instance")
    equipment: Optional[Any] = Field(default=None, description="Equipment instance")
    equipped_items: Dict[str, str] = Field(
        default_factory=dict,
        description="Equipped items by slot (deprecated, use equipment)",
    )

    # Combat
    faction: str = Field(
        default="neutral", description="Entity faction (player, enemy, etc.)"
    )
    can_act: bool = Field(default=True, description="Whether entity can take actions")

    # Position (will be used by world system)
    position: tuple[int, int] = Field(
        default=(0, 0), description="World position (x, y)"
    )

    # AI
    ai: Optional["AIInterface"] = Field(
        default=None, description="AI instance for this entity's behavior"
    )

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

    def take_damage(
        self,
        amount: int,
        source: Optional["Entity"] = None,
        damage_type: str = "physical",
    ) -> int:
        """Take damage from an attack.

        Args:
            amount: Base damage amount
            source: Entity that caused the damage
            damage_type: Type of damage (physical, magic, or custom)

        Returns:
            Actual damage taken after defense and resistance calculations

        Note:
            Damage calculation: final = max(0, starting - defense - (resistance * starting))
            - Defense provides flat reduction
            - Resistance provides percentage reduction (-1.0 to 1.0)
            - Positive resistance reduces damage (0.5 = 50% reduction)
            - Negative resistance increases damage (-0.5 = 50% extra damage, i.e., weakness)
            - Both defense and resistance can be applied simultaneously
        """
        from ..combat.damage_types import DamageTypeManager

        # Ensure damage type is registered (auto-registers in lenient mode)
        DamageTypeManager().ensure_registered(damage_type)

        # Get defense based on damage type
        if damage_type == "physical":
            defense = self.stats.get_stat("physical_defense", 0)
        elif damage_type == "magic":
            defense = self.stats.get_stat("magic_defense", 0)
        else:
            # Custom damage types don't use defense, only resistance
            defense = 0

        # Get resistance for this damage type
        resistance = self.stats.get_resistance(damage_type)

        # Calculate damage: starting - defense - (resistance * starting)
        after_defense = amount - defense
        resistance_reduction = int(resistance * amount)
        final_damage = max(0, after_defense - resistance_reduction)

        # Apply the damage
        self.stats.take_damage(final_damage)

        return final_damage

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
        data = self.model_dump(exclude={"inventory", "equipment"})

        # Serialize inventory if present
        if self.inventory is not None:
            data["inventory"] = self.inventory.to_dict()

        # Serialize equipment if present
        if self.equipment is not None:
            data["equipment"] = self.equipment.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create entity from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Entity instance
        """
        from ..items import Inventory, Equipment

        # Make a copy to avoid modifying original
        data = data.copy()

        # Handle inventory
        inventory_data = data.pop("inventory", None)
        equipment_data = data.pop("equipment", None)

        # Create entity
        entity = cls(**data)

        # Restore inventory if present
        if inventory_data:
            entity.inventory = Inventory.from_dict(inventory_data)

        # Restore equipment if present
        if equipment_data:
            entity.equipment = Equipment.from_dict(equipment_data)

        return entity


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

    def level_up(self, stat_points_per_level: int = 3) -> None:
        """Level up the character.

        Args:
            stat_points_per_level: Number of stat points to award (default: 3)

        This can be overridden to customize stat growth. The default implementation
        gives unallocated stat points that can be spent on any stat. Games can
        override this to auto-allocate, use different point values, or restrict
        what stats can be increased.
        """
        self.stats.level += 1
        self.stats.exp_to_next = int(self.stats.exp_to_next * 1.5)

        # Give stat points for player/game to allocate
        self.stats.stat_points += stat_points_per_level

        # Restore HP/MP to new max values
        self.stats.hp = self.stats.get_max_hp()
        self.stats.mp = self.stats.get_max_mp()

    def allocate_stat_point(self, stat_name: str, amount: int = 1) -> bool:
        """Allocate stat points to increase a stat.

        This method is fully generic - it can increase any stat (primary attributes
        or derived substats). Games can override this to add restrictions.

        Args:
            stat_name: Name of the stat to increase
            amount: Number of points to spend (default: 1)

        Returns:
            True if allocation was successful, False if not enough points

        Example:
            >>> character.allocate_stat_point("strength", 2)  # Increase STR by 2
            >>> character.allocate_stat_point("training_speed", 1)  # Train speed substat
        """
        if self.stats.stat_points < amount:
            return False

        # Spend the points
        self.stats.stat_points -= amount

        # Increase the stat
        self.stats.modify(stat_name, amount)

        return True


class NPC(Entity):
    """Non-player character class.

    NPCs can have dialog, quests, and custom behavior.
    """

    faction: str = Field(default="neutral", description="NPC faction")
    dialog_tree_id: Optional[str] = Field(default=None, description="ID of dialog tree")
    quest_ids: List[str] = Field(
        default_factory=list, description="Quest IDs this NPC offers"
    )
    is_merchant: bool = Field(default=False, description="Whether NPC is a merchant")
    merchant_inventory: List[str] = Field(
        default_factory=list, description="Items for sale"
    )


class Enemy(Entity):
    """Enemy character class.

    Enemies have AI behavior and drop items/exp when defeated.

    The loot_table supports both string references (looked up in LootRegistry)
    and direct Item objects for procedural generation:

    Example:
        >>> from barebones_rpg.items import create_material
        >>>
        >>> # Using string references (requires LootRegistry setup)
        >>> goblin = Enemy(
        ...     name="Goblin",
        ...     loot_table=[
        ...         {"item": "Goblin Bone", "chance": 0.3},
        ...         {"item": "Health Potion", "chance": 0.1}
        ...     ]
        ... )
        >>>
        >>> # Using direct Item objects (code-first)
        >>> goblin = Enemy(
        ...     name="Goblin",
        ...     loot_table=[
        ...         {"item": create_material("Bone", value=5), "chance": 0.3}
        ...     ]
        ... )
    """

    faction: str = Field(default="enemy", description="Enemy faction")
    ai_type: str = Field(default="aggressive", description="AI behavior type")
    exp_reward: int = Field(default=10, description="Experience reward on defeat")
    gold_reward: int = Field(default=5, description="Gold reward on defeat")
    loot_table: List[Dict[str, Any]] = Field(
        default_factory=list,
        description='Loot drops as [{"item": "Name" or Item, "chance": 0.0-1.0}]',
    )
    aggro_range: int = Field(default=5, description="Range at which enemy attacks")
