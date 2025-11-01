"""Combat actions and effects.

This module defines the actions that can be taken during combat.
"""

from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod
from enum import Enum, auto
from pydantic import BaseModel, Field
import random


class ActionType(Enum):
    """Types of combat actions."""

    ATTACK = auto()
    SKILL = auto()
    ITEM = auto()
    RUN = auto()
    CUSTOM = auto()


class ActionResult(BaseModel):
    """Result of a combat action.

    Contains information about what happened when an action was performed.
    """

    success: bool = Field(default=True, description="Whether action executed validly (False = invalid/cannot execute)")
    damage: int = Field(default=0, description="Damage dealt")
    healing: int = Field(default=0, description="Healing done")
    message: str = Field(default="", description="Result message")
    critical: bool = Field(default=False, description="Was a critical hit")
    missed: bool = Field(default=False, description="Did the action miss")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")

    model_config = {"arbitrary_types_allowed": True}


class CombatAction(ABC):
    """Base class for combat actions.

    All combat actions inherit from this and implement execute().
    """

    def __init__(self, action_type: ActionType = ActionType.CUSTOM):
        self.action_type = action_type
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, source: Any, target: Optional[Any], context: Dict[str, Any]) -> ActionResult:
        """Execute the action.

        Args:
            source: Entity performing the action
            target: Target of the action (if any)
            context: Additional context (combat state, etc.)

        Returns:
            Result of the action
        """
        pass

    def can_execute(self, source: Any, context: Dict[str, Any]) -> bool:
        """Check if action can be executed.

        Args:
            source: Entity performing the action
            context: Additional context

        Returns:
            True if action can be performed
        """
        return source.can_perform_action()


class AttackAction(CombatAction):
    """Basic physical attack action."""

    def __init__(self):
        super().__init__(ActionType.ATTACK)
        self.name = "Attack"

    def execute(self, source: Any, target: Optional[Any], context: Dict[str, Any]) -> ActionResult:
        """Execute a physical attack.

        Args:
            source: Attacker
            target: Defender
            context: Combat context

        Returns:
            Attack result
        """
        if target is None:
            return ActionResult(success=False, message="No target selected")

        # Calculate hit chance
        hit_chance = source.stats.accuracy - target.stats.evasion
        if random.randint(1, 100) > hit_chance:
            return ActionResult(
                success=True,
                missed=True,
                message=f"{source.name} attacks {target.name} but misses!"
            )

        # Calculate damage
        base_damage = source.stats.atk

        # Check for critical hit
        is_critical = random.randint(1, 100) <= source.stats.critical
        if is_critical:
            base_damage = int(base_damage * 1.5)

        # Apply damage
        actual_damage = target.take_damage(base_damage, source)

        message = f"{source.name} attacks {target.name} for {actual_damage} damage!"
        if is_critical:
            message += " Critical hit!"

        return ActionResult(
            success=True,
            damage=actual_damage,
            critical=is_critical,
            message=message
        )


class SkillAction(CombatAction):
    """Special skill/ability action.

    This is a flexible action that can be customized.
    """

    def __init__(
        self,
        name: str,
        mp_cost: int,
        effect: Callable,
        targets_enemy: bool = True
    ):
        super().__init__(ActionType.SKILL)
        self.name = name
        self.mp_cost = mp_cost
        self.effect = effect
        self.targets_enemy = targets_enemy

    def can_execute(self, source: Any, context: Dict[str, Any]) -> bool:
        """Check if skill can be used.

        Args:
            source: Entity using skill
            context: Combat context

        Returns:
            True if skill can be used
        """
        return (
            super().can_execute(source, context)
            and source.stats.mp >= self.mp_cost
        )

    def execute(self, source: Any, target: Optional[Any], context: Dict[str, Any]) -> ActionResult:
        """Execute the skill.

        Args:
            source: Entity using skill
            target: Target of skill
            context: Combat context

        Returns:
            Skill result
        """
        if not self.can_execute(source, context):
            return ActionResult(
                success=False,
                message=f"{source.name} doesn't have enough MP!"
            )

        # Deduct MP cost
        source.stats.mp -= self.mp_cost

        # Execute the effect
        result = self.effect(source, target, context)

        return result


class ItemAction(CombatAction):
    """Use an item during combat."""

    def __init__(self, item: Any):
        super().__init__(ActionType.ITEM)
        self.item = item
        self.name = f"Use {item.name}"

    def execute(self, source: Any, target: Optional[Any], context: Dict[str, Any]) -> ActionResult:
        """Use an item.

        Args:
            source: Entity using item
            target: Target of item use
            context: Combat context

        Returns:
            Item use result
        """
        # Use the item
        result = self.item.use(target or source, context)

        message = f"{source.name} uses {self.item.name}!"

        return ActionResult(
            success=True,
            message=message,
            metadata={"item_result": result}
        )


class RunAction(CombatAction):
    """Attempt to flee from combat."""

    def __init__(self):
        super().__init__(ActionType.RUN)
        self.name = "Run"
        self.base_success_rate = 50

    def execute(self, source: Any, target: Optional[Any], context: Dict[str, Any]) -> ActionResult:
        """Attempt to run from combat.

        Args:
            source: Entity trying to run
            target: Enemy (used for speed comparison)
            context: Combat context

        Returns:
            Run attempt result
        """
        # Calculate run success based on speed
        success_rate = self.base_success_rate
        if target and hasattr(target, "stats"):
            speed_diff = source.stats.speed - target.stats.speed
            success_rate += speed_diff * 2  # +2% per speed point

        success_rate = max(10, min(90, success_rate))  # Clamp between 10-90%

        if random.randint(1, 100) <= success_rate:
            return ActionResult(
                success=True,
                message=f"{source.name} successfully ran away!",
                metadata={"fled": True}
            )
        else:
            return ActionResult(
                success=True,
                message=f"{source.name} couldn't get away!",
                metadata={"fled": False}
            )


# Factory for creating common actions

def create_attack_action() -> AttackAction:
    """Create a basic attack action."""
    return AttackAction()


def create_skill_action(
    name: str,
    mp_cost: int,
    damage_multiplier: float = 1.5,
    targets_enemy: bool = True
) -> SkillAction:
    """Create a damage skill.

    Args:
        name: Skill name
        mp_cost: MP cost
        damage_multiplier: Damage multiplier vs normal attack
        targets_enemy: Whether skill targets enemies

    Returns:
        Skill action
    """
    def effect(source, target, context):
        if target is None:
            return ActionResult(success=False, message="No target selected")

        base_damage = int(source.stats.atk * damage_multiplier)
        actual_damage = target.take_damage(base_damage, source)

        return ActionResult(
            success=True,
            damage=actual_damage,
            message=f"{source.name} uses {name} on {target.name} for {actual_damage} damage!"
        )

    return SkillAction(name, mp_cost, effect, targets_enemy)


def create_heal_skill(name: str, mp_cost: int, heal_amount: int) -> SkillAction:
    """Create a healing skill.

    Args:
        name: Skill name
        mp_cost: MP cost
        heal_amount: Amount to heal

    Returns:
        Healing skill action
    """
    def effect(source, target, context):
        actual_heal = target.heal(heal_amount)
        return ActionResult(
            success=True,
            healing=actual_heal,
            message=f"{source.name} uses {name} on {target.name} for {actual_heal} HP!"
        )

    return SkillAction(name, mp_cost, effect, targets_enemy=False)
