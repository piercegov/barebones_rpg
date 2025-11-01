"""Combat actions and effects.

This module defines the actions that can be taken during combat.
"""

from typing import Optional, Dict, Any, Callable, List
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
    Supports both single-target and multi-target actions.
    """

    success: bool = Field(
        default=True,
        description="Whether action executed validly (False = invalid/cannot execute)",
    )
    damage: int = Field(default=0, description="Total damage dealt")
    healing: int = Field(default=0, description="Total healing done")
    message: str = Field(default="", description="Result message")
    critical: bool = Field(default=False, description="Was a critical hit")
    missed: bool = Field(default=False, description="Did the action miss")
    targets_hit: List[Any] = Field(
        default_factory=list, description="List of targets affected by this action"
    )
    target_results: Dict[str, Any] = Field(
        default_factory=dict, description="Per-target breakdown (optional)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional data"
    )

    model_config = {"arbitrary_types_allowed": True}


class CombatAction(ABC):
    """Base class for combat actions.

    All combat actions inherit from this and implement execute().
    Actions now accept a list of targets to support both single-target
    and multi-target (AOE) abilities.
    """

    def __init__(self, action_type: ActionType = ActionType.CUSTOM):
        self.action_type = action_type
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(
        self, source: Any, targets: List[Any], context: Dict[str, Any]
    ) -> ActionResult:
        """Execute the action.

        Args:
            source: Entity performing the action
            targets: List of target entities (empty list for self-only actions)
            context: Additional context (combat state, etc.)

        Returns:
            Result of the action

        Note:
            For single-target actions, use targets[0] (after checking the list isn't empty).
            For multi-target actions, iterate through all targets in the list.
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

    def calculate_damage(
        self,
        source: Any,
        target: Optional[Any],
        weapon: Optional[Any],
        context: Dict[str, Any],
    ) -> tuple[int, str]:
        """Calculate base damage before crits and defense.

        Override this method to add proficiency systems or other damage modifiers.

        Args:
            source: Attacker
            target: Defender
            weapon: Equipped weapon (or None for unarmed)
            context: Combat context

        Returns:
            Tuple of (damage_amount, damage_type)
        """
        if weapon is None:
            # Unarmed attack - just use strength
            return source.stats.get_stat("strength", 10), "physical"

        # Get damage type from weapon
        damage_type = weapon.damage_type

        # Select appropriate attribute based on damage type
        if damage_type == "magic":
            stat_value = source.stats.get_stat("intelligence", 10)
        else:  # physical or any other type defaults to strength
            stat_value = source.stats.get_stat("strength", 10)

        # Calculate total damage
        total_damage = stat_value + weapon.base_damage

        return total_damage, damage_type

    def execute(
        self, source: Any, targets: List[Any], context: Dict[str, Any]
    ) -> ActionResult:
        """Execute a physical attack.

        By default, attacks the first target in the list (single-target).
        Can be extended for cleave/multi-target attacks.

        Args:
            source: Attacker
            targets: List of target entities
            context: Combat context

        Returns:
            Attack result
        """
        if not targets:
            return ActionResult(success=False, message="No target selected")

        target = targets[0]

        # Get equipped weapon
        weapon = None
        if hasattr(source, "equipment") and source.equipment is not None:
            from ..items.item import EquipSlot

            weapon = source.equipment.get_equipped(EquipSlot.WEAPON)

        # Check range if both entities have positions and weapon has range
        if weapon and hasattr(weapon, "range") and weapon.range > 0:
            if hasattr(source, "position") and hasattr(target, "position"):
                from .targeting import manhattan_distance

                distance = manhattan_distance(source.position, target.position)
                if distance > weapon.range:
                    return ActionResult(
                        success=False,
                        message=f"{target.name} is out of range! (distance: {distance}, weapon range: {weapon.range})",
                    )

        # Calculate hit chance
        hit_chance = source.stats.get_stat("accuracy", 90) - target.stats.get_stat(
            "evasion", 5
        )
        if random.randint(1, 100) > hit_chance:
            return ActionResult(
                success=True,
                missed=True,
                message=f"{source.name} attacks {target.name} but misses!",
                targets_hit=[],
            )

        # Calculate damage using the hookable method
        base_damage, damage_type = self.calculate_damage(
            source, target, weapon, context
        )

        # Check for critical hit
        is_critical = random.randint(1, 100) <= source.stats.get_stat("critical", 5)
        if is_critical:
            base_damage = int(base_damage * 1.5)

        # Apply damage with damage type
        actual_damage = target.take_damage(base_damage, source, damage_type)

        message = f"{source.name} attacks {target.name} for {actual_damage} damage!"
        if is_critical:
            message += " Critical hit!"

        return ActionResult(
            success=True,
            damage=actual_damage,
            critical=is_critical,
            message=message,
            targets_hit=[target],
            metadata={"damage_type": damage_type},
        )


class SkillAction(CombatAction):
    """Special skill/ability action.

    This is a flexible action that can be customized.
    """

    def __init__(
        self, name: str, mp_cost: int, effect: Callable, targets_enemy: bool = True
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
        return super().can_execute(source, context) and source.stats.mp >= self.mp_cost

    def execute(
        self, source: Any, targets: List[Any], context: Dict[str, Any]
    ) -> ActionResult:
        """Execute the skill.

        Args:
            source: Entity using skill
            targets: List of target entities
            context: Combat context

        Returns:
            Skill result
        """
        if not self.can_execute(source, context):
            return ActionResult(
                success=False, message=f"{source.name} doesn't have enough MP!"
            )

        # Deduct MP cost
        source.stats.mp -= self.mp_cost

        # Execute the effect (effect function receives the full target list)
        result = self.effect(source, targets, context)

        return result


class ItemAction(CombatAction):
    """Use an item during combat."""

    def __init__(self, item: Any):
        super().__init__(ActionType.ITEM)
        self.item = item
        self.name = f"Use {item.name}"

    def execute(
        self, source: Any, targets: List[Any], context: Dict[str, Any]
    ) -> ActionResult:
        """Use an item.

        Args:
            source: Entity using item
            targets: List of target entities (uses first target or source if empty)
            context: Combat context

        Returns:
            Item use result
        """
        # Use the item on first target, or source if no targets
        target = targets[0] if targets else source
        result = self.item.use(target, context)

        message = f"{source.name} uses {self.item.name}!"

        return ActionResult(
            success=True,
            message=message,
            targets_hit=[target],
            metadata={"item_result": result},
        )


class RunAction(CombatAction):
    """Attempt to flee from combat."""

    def __init__(self):
        super().__init__(ActionType.RUN)
        self.name = "Run"
        self.base_success_rate = 50

    def execute(
        self, source: Any, targets: List[Any], context: Dict[str, Any]
    ) -> ActionResult:
        """Attempt to run from combat.

        Args:
            source: Entity trying to run
            targets: List of enemies (uses first for speed comparison if available)
            context: Combat context

        Returns:
            Run attempt result
        """
        # Calculate run success based on speed
        success_rate = self.base_success_rate
        if targets and hasattr(targets[0], "stats"):
            speed_diff = source.stats.speed - targets[0].stats.speed
            success_rate += speed_diff * 2  # +2% per speed point

        success_rate = max(10, min(90, success_rate))  # Clamp between 10-90%

        if random.randint(1, 100) <= success_rate:
            return ActionResult(
                success=True,
                message=f"{source.name} successfully ran away!",
                metadata={"fled": True},
            )
        else:
            return ActionResult(
                success=True,
                message=f"{source.name} couldn't get away!",
                metadata={"fled": False},
            )


# Factory for creating common actions


def create_attack_action() -> AttackAction:
    """Create a basic attack action."""
    return AttackAction()


def create_skill_action(
    name: str,
    mp_cost: int,
    damage_multiplier: float = 1.5,
    damage_type: str = "physical",
    targets_enemy: bool = True,
    max_targets: int = 1,
) -> SkillAction:
    """Create a damage skill.

    Args:
        name: Skill name
        mp_cost: MP cost
        damage_multiplier: Damage multiplier vs normal attack
        damage_type: Type of damage (physical, magic, or custom)
        targets_enemy: Whether skill targets enemies
        max_targets: Maximum number of targets to hit (1=single target, 2=cleave, None=unlimited AOE)

    Returns:
        Skill action

    Example:
        >>> # Single-target skill
        >>> fireball = create_skill_action("Fireball", mp_cost=10, damage_multiplier=2.0, damage_type="magic")
        >>>
        >>> # Cleave attack (hits 2 targets)
        >>> cleave = create_skill_action("Cleave", mp_cost=5, damage_multiplier=1.2, max_targets=2)
        >>>
        >>> # AOE skill that hits all targets
        >>> meteor = create_skill_action("Meteor", mp_cost=25, damage_multiplier=1.5, damage_type="magic", max_targets=None)
    """

    def effect(source, targets, context):
        if not targets:
            return ActionResult(success=False, message="No target selected")

        # Select stat based on damage type
        if damage_type == "magic":
            stat_value = source.stats.get_stat("intelligence", 10)
        else:
            stat_value = source.stats.get_stat("strength", 10)

        base_damage = int(stat_value * damage_multiplier)

        # Determine which targets to hit based on max_targets
        if max_targets is None:
            targets_to_hit = targets
        else:
            targets_to_hit = targets[:max_targets]

        total_damage = 0
        targets_hit = []
        messages = []

        for target in targets_to_hit:
            actual_damage = target.take_damage(base_damage, source, damage_type)
            total_damage += actual_damage
            targets_hit.append(target)
            messages.append(f"{target.name} for {actual_damage} damage")

        if len(targets_hit) == 1:
            message = f"{source.name} uses {name} on {messages[0]}!"
        else:
            message = f"{source.name} uses {name} hitting {', '.join(messages)}!"

        return ActionResult(
            success=True,
            damage=total_damage,
            message=message,
            targets_hit=targets_hit,
            metadata={"damage_type": damage_type},
        )

    return SkillAction(name, mp_cost, effect, targets_enemy)


def create_heal_skill(
    name: str, mp_cost: int, heal_amount: int, max_targets: int = 1
) -> SkillAction:
    """Create a healing skill.

    Args:
        name: Skill name
        mp_cost: MP cost
        heal_amount: Amount to heal per target
        max_targets: Maximum number of targets to heal (1=single target, None=unlimited group heal)

    Returns:
        Healing skill action

    Example:
        >>> # Single-target heal
        >>> cure = create_heal_skill("Cure", mp_cost=5, heal_amount=30)
        >>>
        >>> # Group heal (heals 3 targets)
        >>> group_heal = create_heal_skill("Group Heal", mp_cost=15, heal_amount=20, max_targets=3)
        >>>
        >>> # Mass heal (heals all targets)
        >>> mass_heal = create_heal_skill("Mass Heal", mp_cost=25, heal_amount=15, max_targets=None)
    """

    def effect(source, targets, context):
        if not targets:
            # If no targets specified, heal self
            targets = [source]

        # Determine which targets to heal based on max_targets
        if max_targets is None:
            targets_to_heal = targets
        else:
            targets_to_heal = targets[:max_targets]

        total_healing = 0
        targets_hit = []
        messages = []

        for target in targets_to_heal:
            actual_heal = target.heal(heal_amount)
            total_healing += actual_heal
            targets_hit.append(target)
            messages.append(f"{target.name} for {actual_heal} HP")

        if len(targets_hit) == 1:
            message = f"{source.name} uses {name} on {messages[0]}!"
        else:
            message = f"{source.name} uses {name} healing {', '.join(messages)}!"

        return ActionResult(
            success=True,
            healing=total_healing,
            message=message,
            targets_hit=targets_hit,
        )

    return SkillAction(name, mp_cost, effect, targets_enemy=False)
