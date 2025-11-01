"""Stats system for entities.

This module provides the stats system used by all entities (characters, NPCs, enemies).
Stats are flexible and can be extended for different game types.
"""

from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class Stats(BaseModel):
    """Base stats for an entity.

    This can be extended with additional stats for specific game types.
    All stats have a current value and an optional max value.

    Example:
        >>> stats = Stats(hp=100, mp=50, atk=10, defense=5)
        >>> stats.hp -= 20
        >>> print(stats.hp)
        80
        >>> stats.modify("atk", 5)  # Increase attack by 5
        >>> print(stats.atk)
        15
    """

    # Core stats
    hp: int = Field(default=100, description="Hit points (health)")
    max_hp: int = Field(default=100, description="Maximum hit points")
    mp: int = Field(default=0, description="Magic/mana points")
    max_mp: int = Field(default=0, description="Maximum magic points")

    # Combat stats
    atk: int = Field(default=10, description="Attack power")
    defense: int = Field(default=5, description="Defense")
    magic_atk: int = Field(default=0, description="Magic attack power")
    magic_def: int = Field(default=0, description="Magic defense")
    speed: int = Field(default=10, description="Speed (determines turn order)")
    accuracy: int = Field(default=90, description="Hit accuracy percentage")
    evasion: int = Field(default=5, description="Evasion percentage")
    critical: int = Field(default=5, description="Critical hit chance percentage")

    # Level/Experience
    level: int = Field(default=1, description="Character level")
    exp: int = Field(default=0, description="Experience points")
    exp_to_next: int = Field(default=100, description="Experience needed for next level")

    # Custom stats (for extensibility)
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom stats")

    model_config = {"extra": "allow"}  # Allow additional fields

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
        """Get a stat value.

        Args:
            stat_name: Name of the stat
            default: Default value if stat doesn't exist

        Returns:
            The stat value
        """
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
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp

    def restore_mp(self, amount: int) -> int:
        """Restore MP, capped at max_mp.

        Args:
            amount: Amount to restore

        Returns:
            Actual amount restored
        """
        old_mp = self.mp
        self.mp = min(self.mp + amount, self.max_mp)
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
