"""Stats system for entities.

This module provides the stats system used by all entities (characters, NPCs, enemies).
Stats are flexible and can be extended for different game types.
"""

from typing import Dict, Optional, Any, Callable
from pydantic import BaseModel, Field


class Stats(BaseModel):
    """Base stats for an entity using attribute-based system.

    Primary Attributes (core stats that determine derived values):
    - STR (Strength): Physical damage, melee power
    - CON (Constitution): HP, physical defense
    - INT (Intelligence): Magic damage, MP, magic defense
    - DEX (Dexterity): Speed, accuracy, evasion, critical chance
    - CHA (Charisma): Dialog, persuasion, prices

    Derived Substats are calculated from attributes + training bonuses.

    Example:
        >>> stats = Stats(strength=15, constitution=12, intelligence=10)
        >>> stats.hp -= 20
        >>> print(stats.hp)
        100
        >>> stats.allocate_stat_points("strength", 2)  # Direct allocation
        >>> print(stats.strength)
        17
    """

    # Primary Attributes
    strength: int = Field(default=10, description="Strength (physical damage)")
    constitution: int = Field(
        default=10, description="Constitution (HP, physical defense)"
    )
    intelligence: int = Field(default=10, description="Intelligence (magic damage, MP)")
    dexterity: int = Field(
        default=10, description="Dexterity (speed, accuracy, evasion)"
    )
    charisma: int = Field(default=10, description="Charisma (dialog, persuasion)")

    # HP/MP (still direct values for current state)
    hp: int = Field(default=100, description="Current hit points")
    mp: int = Field(default=0, description="Current magic/mana points")

    # Derived Substat Base Values (before attribute bonuses)
    base_max_hp: int = Field(default=50, description="Base max HP before CON bonus")
    base_max_mp: int = Field(default=20, description="Base max MP before INT bonus")
    base_physical_defense: int = Field(
        default=0, description="Base physical defense before CON bonus"
    )
    base_magic_defense: int = Field(
        default=0, description="Base magic defense before INT bonus"
    )
    base_speed: int = Field(default=5, description="Base speed before DEX bonus")
    base_accuracy: int = Field(default=80, description="Base accuracy before DEX bonus")
    base_evasion: int = Field(default=5, description="Base evasion before DEX bonus")
    base_critical: int = Field(
        default=5, description="Base critical chance before DEX bonus"
    )

    # Training bonuses (independent improvements to substats)
    training_physical_defense: int = Field(
        default=0, description="Trained physical defense bonus"
    )
    training_magic_defense: int = Field(
        default=0, description="Trained magic defense bonus"
    )
    training_speed: int = Field(default=0, description="Trained speed bonus")
    training_accuracy: int = Field(default=0, description="Trained accuracy bonus")
    training_evasion: int = Field(default=0, description="Trained evasion bonus")
    training_critical: int = Field(default=0, description="Trained critical bonus")

    # Attribute -> Substat multipliers (how much each attribute point contributes)
    hp_per_con: int = Field(default=5, description="HP gained per CON point")
    mp_per_int: int = Field(default=3, description="MP gained per INT point")
    defense_per_con: float = Field(
        default=0.5, description="Physical defense per CON point"
    )
    magic_def_per_int: float = Field(
        default=0.5, description="Magic defense per INT point"
    )
    speed_per_dex: float = Field(default=0.5, description="Speed per DEX point")
    accuracy_per_dex: float = Field(default=0.5, description="Accuracy per DEX point")
    evasion_per_dex: float = Field(default=0.3, description="Evasion per DEX point")
    critical_per_dex: float = Field(
        default=0.3, description="Critical chance per DEX point"
    )

    # Level/Experience
    level: int = Field(default=1, description="Character level")
    exp: int = Field(default=0, description="Experience points")
    exp_to_next: int = Field(
        default=100, description="Experience needed for next level"
    )
    stat_points: int = Field(default=0, description="Unallocated stat points")

    # Custom stats (for extensibility - proficiencies, etc.)
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom stats")

    # Damage resistances (percentage-based damage reduction)
    resistances: Dict[str, float] = Field(
        default_factory=dict,
        description="Damage type resistances (-1.0 to 1.0: negative = weakness, positive = resistance)",
    )

    model_config = {"extra": "allow"}  # Allow additional fields

    def model_post_init(self, __context):
        """Initialize max HP/MP after creation if not explicitly set."""
        # Only auto-set HP/MP if they match the default values AND weren't explicitly provided
        # This is a heuristic - if user wants different behavior, they can set hp/mp after creation
        pass  # Removed auto-initialization to avoid unexpected behavior

    # Calculated property methods for derived substats
    def get_max_hp(self) -> int:
        """Calculate effective max HP."""
        return self.base_max_hp + (self.constitution * self.hp_per_con)

    def get_max_mp(self) -> int:
        """Calculate effective max MP."""
        return self.base_max_mp + (self.intelligence * self.mp_per_int)

    def get_physical_defense(self) -> int:
        """Calculate effective physical defense."""
        return int(
            self.base_physical_defense
            + (self.constitution * self.defense_per_con)
            + self.training_physical_defense
        )

    def get_magic_defense(self) -> int:
        """Calculate effective magic defense."""
        return int(
            self.base_magic_defense
            + (self.intelligence * self.magic_def_per_int)
            + self.training_magic_defense
        )

    def get_speed(self) -> int:
        """Calculate effective speed."""
        return int(
            self.base_speed
            + (self.dexterity * self.speed_per_dex)
            + self.training_speed
        )

    def get_accuracy(self) -> int:
        """Calculate effective accuracy."""
        return int(
            self.base_accuracy
            + (self.dexterity * self.accuracy_per_dex)
            + self.training_accuracy
        )

    def get_evasion(self) -> int:
        """Calculate effective evasion."""
        return int(
            self.base_evasion
            + (self.dexterity * self.evasion_per_dex)
            + self.training_evasion
        )

    def get_critical(self) -> int:
        """Calculate effective critical chance."""
        return int(
            self.base_critical
            + (self.dexterity * self.critical_per_dex)
            + self.training_critical
        )

    # Convenience properties for backward compatibility
    @property
    def max_hp(self) -> int:
        """Max HP property for backward compatibility."""
        return self.get_max_hp()

    @property
    def max_mp(self) -> int:
        """Max MP property for backward compatibility."""
        return self.get_max_mp()

    @property
    def physical_defense(self) -> int:
        """Physical defense property."""
        return self.get_physical_defense()

    @property
    def magic_defense(self) -> int:
        """Magic defense property."""
        return self.get_magic_defense()

    @property
    def speed(self) -> int:
        """Speed property."""
        return self.get_speed()

    @property
    def accuracy(self) -> int:
        """Accuracy property."""
        return self.get_accuracy()

    @property
    def evasion(self) -> int:
        """Evasion property."""
        return self.get_evasion()

    @property
    def critical(self) -> int:
        """Critical chance property."""
        return self.get_critical()

    def modify(self, stat_name: str, amount: int) -> None:
        """Modify a stat by a given amount.

        Args:
            stat_name: Name of the stat to modify
            amount: Amount to change (positive or negative)
        """
        if hasattr(self, stat_name):
            current = getattr(self, stat_name)
            setattr(self, stat_name, current + amount)
        elif stat_name in self.custom:
            self.custom[stat_name] += amount
        else:
            self.custom[stat_name] = amount

    def set_stat(self, stat_name: str, value: int) -> bool:
        """Set a stat to a specific value.

        Args:
            stat_name: Name of the stat to set
            value: New value

        Returns:
            True if stat was set successfully
        """
        if hasattr(self, stat_name):
            setattr(self, stat_name, value)
        else:
            self.custom[stat_name] = value
        return True

    def get_stat(self, stat_name: str, default: int = 0) -> int:
        """Get a stat value, including derived stats.

        Args:
            stat_name: Name of the stat
            default: Default value if stat doesn't exist

        Returns:
            The stat value
        """
        # Handle derived stats with getter methods
        if stat_name == "max_hp":
            return self.get_max_hp()
        elif stat_name == "max_mp":
            return self.get_max_mp()
        elif (
            stat_name == "physical_defense" or stat_name == "defense"
        ):  # "defense" for backward compat
            return self.get_physical_defense()
        elif stat_name == "magic_defense":
            return self.get_magic_defense()
        elif stat_name == "speed":
            return self.get_speed()
        elif stat_name == "accuracy":
            return self.get_accuracy()
        elif stat_name == "evasion":
            return self.get_evasion()
        elif stat_name == "critical":
            return self.get_critical()

        # Regular stats
        if hasattr(self, stat_name):
            return getattr(self, stat_name)
        return self.custom.get(stat_name, default)

    def restore_hp(self, amount: int) -> int:
        """Restore HP, capped at max_hp.

        Args:
            amount: Amount to restore

        Returns:
            Actual amount restored
        """
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.get_max_hp())
        return self.hp - old_hp

    def restore_mp(self, amount: int) -> int:
        """Restore MP, capped at max_mp.

        Args:
            amount: Amount to restore

        Returns:
            Actual amount restored
        """
        old_mp = self.mp
        self.mp = min(self.mp + amount, self.get_max_mp())
        return self.mp - old_mp

    def take_damage(self, amount: int) -> int:
        """Take damage, reducing HP.

        Args:
            amount: Damage amount

        Returns:
            Actual damage taken
        """
        old_hp = self.hp
        self.hp = max(0, self.hp - amount)
        return old_hp - self.hp

    def is_alive(self) -> bool:
        """Check if entity is alive (HP > 0)."""
        return self.hp > 0

    def is_dead(self) -> bool:
        """Check if entity is dead (HP <= 0)."""
        return self.hp <= 0

    def get_resistance(self, damage_type: str) -> float:
        """Get resistance value for a damage type.

        Args:
            damage_type: Name of the damage type

        Returns:
            Resistance value (-1.0 to 1.0):
            - Positive values = resistance (0.5 = 50% damage reduction)
            - Negative values = weakness (-0.5 = 50% extra damage)
            - 0.0 = no resistance or weakness
        """
        return self.resistances.get(damage_type, 0.0)

    def set_resistance(self, damage_type: str, value: float) -> None:
        """Set resistance for a damage type.

        Args:
            damage_type: Name of the damage type
            value: Resistance value (-1.0 to 1.0):
                   Positive = resistance, Negative = weakness
        """
        self.resistances[damage_type] = value

    def modify_resistance(self, damage_type: str, delta: float) -> None:
        """Modify resistance for a damage type by a delta.

        Args:
            damage_type: Name of the damage type
            delta: Amount to change resistance by (can be positive or negative)
        """
        current = self.get_resistance(damage_type)
        self.resistances[damage_type] = current + delta


class StatusEffect(BaseModel):
    """A status effect that can be applied to an entity.

    Examples: poisoned, stunned, buffed, etc.
    """

    name: str = Field(description="Name of the status effect")
    duration: int = Field(default=-1, description="Duration in turns (-1 = permanent)")
    stat_modifiers: Dict[str, int] = Field(
        default_factory=dict, description="Stat modifiers while active"
    )
    on_turn: Optional[Callable] = Field(
        default=None, description="Function called each turn"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional data"
    )

    model_config = {"arbitrary_types_allowed": True}

    def tick(self) -> bool:
        """Process one turn of the status effect.

        Returns:
            True if effect should continue, False if it expired
        """
        if self.duration > 0:
            self.duration -= 1
            return self.duration > 0
        return self.duration == -1  # Permanent effects never expire


class StatsManager:
    """Manages stats and status effects for an entity.

    This provides a layer on top of Stats that handles temporary modifiers,
    status effects, and stat change events.
    """

    def __init__(self, base_stats: Stats):
        """Initialize the stats manager.

        Args:
            base_stats: The base stats for the entity
        """
        self.base_stats = base_stats
        self.status_effects: list[StatusEffect] = []
        self._stat_change_callbacks: list[Callable] = []

    def get_effective_stat(self, stat_name: str, default: int = 0) -> int:
        """Get the effective value of a stat including all modifiers.

        Args:
            stat_name: Name of the stat
            default: Default value if stat doesn't exist

        Returns:
            The effective stat value
        """
        base_value = self.base_stats.get_stat(stat_name, default)

        # Apply status effect modifiers
        for effect in self.status_effects:
            if stat_name in effect.stat_modifiers:
                base_value += effect.stat_modifiers[stat_name]

        return base_value

    def add_status_effect(self, effect: StatusEffect) -> bool:
        """Add a status effect.

        Args:
            effect: The status effect to add

        Returns:
            True if status effect was added successfully
        """
        self.status_effects.append(effect)
        return True

    def remove_status_effect(self, effect_name: str) -> bool:
        """Remove a status effect by name.

        Args:
            effect_name: Name of the effect to remove

        Returns:
            True if effect was found and removed
        """
        for effect in self.status_effects:
            if effect.name == effect_name:
                self.status_effects.remove(effect)
                return True
        return False

    def process_status_effects(self) -> None:
        """Process all status effects for one turn."""
        expired = []
        for effect in self.status_effects:
            if effect.on_turn:
                effect.on_turn(self.base_stats)
            if not effect.tick():
                expired.append(effect)

        # Remove expired effects
        for effect in expired:
            self.status_effects.remove(effect)

    def has_status(self, effect_name: str) -> bool:
        """Check if entity has a specific status effect.

        Args:
            effect_name: Name of the status effect

        Returns:
            True if entity has the effect
        """
        return any(effect.name == effect_name for effect in self.status_effects)

    def on_stat_change(self, callback: Callable) -> None:
        """Subscribe to stat change events.

        Args:
            callback: Function to call when stats change
        """
        self._stat_change_callbacks.append(callback)
