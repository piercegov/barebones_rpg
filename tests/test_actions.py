"""Tests for combat actions."""

import pytest
import random
from barebones_rpg.combat.actions import (
    AttackAction,
    SkillAction,
    RunAction,
    ActionResult,
)
from barebones_rpg.combat.combat import Combat
from barebones_rpg.entities.entity import Character, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.core.events import EventManager


@pytest.fixture
def attacker_and_target():
    """Create an attacker and target for testing."""
    attacker = Character(
        name="Hero",
        stats=Stats(
            strength=20,
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            hp=100,
        ),
    )
    target = Enemy(
        name="Goblin",
        stats=Stats(
            strength=8, constitution=8, intelligence=5, dexterity=12, charisma=5, hp=50
        ),
    )
    return attacker, target


def test_attack_with_no_target_returns_failure():
    """Attack with no target should return failure."""
    attacker = Character(name="Hero", stats=Stats(strength=15))
    action = AttackAction()

    result = action.execute(attacker, [], {})

    assert result.success is False
    assert result.message == "No target selected"


def test_attack_misses_based_on_accuracy(attacker_and_target, monkeypatch):
    """Attack should miss based on accuracy/evasion calculation."""
    attacker, target = attacker_and_target
    action = AttackAction()

    def always_miss(a, b):
        return 100

    monkeypatch.setattr(random, "randint", always_miss)

    result = action.execute(attacker, [target], {})

    assert result.success is True
    assert result.missed is True
    assert result.damage == 0


def test_attack_hits_and_deals_damage(attacker_and_target, monkeypatch):
    """Attack should hit and deal damage."""
    attacker, target = attacker_and_target
    action = AttackAction()

    def always_hit_no_crit(a, b):
        if a == 1 and b == 100:
            return 50
        return 100

    monkeypatch.setattr(random, "randint", always_hit_no_crit)

    old_hp = target.stats.hp
    result = action.execute(attacker, [target], {})

    assert result.success is True
    assert not result.missed
    assert result.damage > 0
    assert target.stats.hp < old_hp


def test_critical_hits_apply_multiplier(attacker_and_target, monkeypatch):
    """Critical hits should apply correct damage multiplier."""
    attacker, target = attacker_and_target
    action = AttackAction()

    call_count = {"count": 0}

    def deterministic(a, b):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return 50
        # Second call is crit check - return low value to crit
        return 1

    monkeypatch.setattr(random, "randint", deterministic)

    result = action.execute(attacker, [target], {})

    assert result.critical is True
    assert result.damage > 0


def test_skill_mp_cost_prevents_execution():
    """Skill with insufficient MP should fail to execute."""
    caster = Character(name="Mage", stats=Stats(intelligence=12, base_max_mp=20, mp=10))
    target = Enemy(name="Goblin", stats=Stats(hp=50))

    def skill_effect(source, targets, context):
        return ActionResult(success=True, damage=30, targets_hit=targets)

    skill = SkillAction("Fireball", mp_cost=20, effect=skill_effect)

    result = skill.execute(caster, [target], {})

    assert result.success is False
    assert "doesn't have enough MP" in result.message


def test_skill_executes_with_sufficient_mp():
    """Skill should execute when caster has enough MP."""
    caster = Character(
        name="Mage", stats=Stats(strength=15, intelligence=12, base_max_mp=20, mp=50)
    )
    target = Enemy(
        name="Goblin", stats=Stats(constitution=0, hp=50)
    )  # 0 CON = 0 defense

    def skill_effect(source, targets, context):
        damage = targets[0].take_damage(30, source)
        return ActionResult(
            success=True, damage=damage, message="Fireball!", targets_hit=targets
        )

    skill = SkillAction("Fireball", mp_cost=20, effect=skill_effect)

    result = skill.execute(caster, [target], {})

    assert result.success is True
    assert caster.stats.mp == 30
    assert target.stats.hp == 20


def test_run_action_success_rate_with_speed_difference(monkeypatch):
    """Run action success rate should be affected by speed difference."""
    fast_runner = Character(name="Fast", stats=Stats(dexterity=20))
    slow_enemy = Enemy(name="Slow", stats=Stats(dexterity=10))

    def favorable_roll(a, b):
        return 50

    monkeypatch.setattr(random, "randint", favorable_roll)

    action = RunAction()
    result = action.execute(fast_runner, [slow_enemy], {})

    assert result.success is True
    assert result.metadata.get("fled") is True


def test_run_action_fails(monkeypatch):
    """Run action can fail."""
    runner = Character(name="Runner", stats=Stats(dexterity=10))
    enemy = Enemy(name="Enemy", stats=Stats(dexterity=10))

    def unfavorable_roll(a, b):
        return 100

    monkeypatch.setattr(random, "randint", unfavorable_roll)

    action = RunAction()
    result = action.execute(runner, [enemy], {})

    assert result.success is True
    assert result.metadata.get("fled") is False


def test_skill_can_execute_checks_mp():
    """Skill can_execute should check MP availability."""
    low_mp_caster = Character(name="Tired Mage", stats=Stats(mp=5))

    def dummy_effect(source, targets, context):
        return ActionResult(success=True, targets_hit=targets)

    skill = SkillAction("Expensive Spell", mp_cost=20, effect=dummy_effect)

    can_execute = skill.can_execute(low_mp_caster, {})

    assert can_execute is False


def test_attack_action_calculates_damage_correctly():
    """Attack action should calculate damage as strength - defense with minimum 1."""
    attacker = Character(
        name="Hero",
        stats=Stats(strength=15, dexterity=18, base_accuracy=100, base_critical=0),
    )
    target = Enemy(
        name="Tank",
        stats=Stats(constitution=12, dexterity=10, hp=100, base_physical_defense=5),
    )

    action = AttackAction()
    result = action.execute(attacker, [target], {})

    assert result.damage >= 1


def test_attack_action_calculates_damage_correctly_atk_lower():
    """Attack action should calculate damage with defense and resistance, minimum 0."""
    attacker = Character(
        name="Hero",
        stats=Stats(strength=5, dexterity=18, base_accuracy=100, base_critical=0),
    )
    target = Enemy(
        name="Tank",
        stats=Stats(constitution=12, dexterity=10, hp=100, base_physical_defense=5),
    )

    action = AttackAction()
    result = action.execute(attacker, [target], {})

    # Damage: 5 (STR) - (5 base + 6 from CON) = 5 - 11 = 0 (clamped to 0)
    assert result.damage == 0


def test_skill_action_deducts_mp_cost():
    """SkillAction should deduct MP cost when executed."""
    caster = Character(name="Mage", stats=Stats(intelligence=12, base_max_mp=20, mp=50))
    target = Enemy(name="Goblin", stats=Stats(hp=50))

    def skill_effect(source, targets, context):
        return ActionResult(success=True, message="Boom!", targets_hit=targets)

    skill = SkillAction("Magic Missile", mp_cost=15, effect=skill_effect)

    old_mp = caster.stats.mp
    result = skill.execute(caster, [target], {})

    assert caster.stats.mp == old_mp - 15


def test_aoe_skill_hits_all_targets():
    """AOE skill should hit all targets in the list."""
    from barebones_rpg.combat.actions import create_skill_action

    caster = Character(name="Mage", stats=Stats(intelligence=20, base_max_mp=50, mp=50))
    enemy1 = Enemy(name="Goblin1", stats=Stats(constitution=0, hp=30))
    enemy2 = Enemy(name="Goblin2", stats=Stats(constitution=0, hp=30))
    enemy3 = Enemy(name="Goblin3", stats=Stats(constitution=0, hp=30))

    # Create AOE skill with max_targets=None (unlimited)
    fireball = create_skill_action(
        "Fireball",
        mp_cost=15,
        damage_multiplier=1.0,
        damage_type="magic",
        max_targets=None,
    )

    result = fireball.execute(caster, [enemy1, enemy2, enemy3], {})

    assert result.success
    assert len(result.targets_hit) == 3
    assert enemy1 in result.targets_hit
    assert enemy2 in result.targets_hit
    assert enemy3 in result.targets_hit
    assert enemy1.stats.hp < 30
    assert enemy2.stats.hp < 30
    assert enemy3.stats.hp < 30


def test_single_target_skill_hits_first_target_only():
    """Single-target skill should only hit the first target in the list."""
    from barebones_rpg.combat.actions import create_skill_action

    caster = Character(name="Mage", stats=Stats(intelligence=20, base_max_mp=50, mp=50))
    enemy1 = Enemy(name="Goblin1", stats=Stats(constitution=0, hp=30))
    enemy2 = Enemy(name="Goblin2", stats=Stats(constitution=0, hp=30))

    # Create single-target skill (max_targets=1 by default)
    magic_missile = create_skill_action(
        "Magic Missile", mp_cost=5, damage_multiplier=1.0, damage_type="magic"
    )

    result = magic_missile.execute(caster, [enemy1, enemy2], {})

    assert result.success
    assert len(result.targets_hit) == 1
    assert enemy1 in result.targets_hit
    assert enemy2 not in result.targets_hit
    assert enemy1.stats.hp < 30
    assert enemy2.stats.hp == 30  # Second target not affected


def test_aoe_heal_heals_all_targets():
    """AOE heal should heal all targets in the list."""
    from barebones_rpg.combat.actions import create_heal_skill

    healer = Character(name="Cleric", stats=Stats(base_max_mp=50, mp=50))
    ally1 = Character(name="Warrior", stats=Stats(base_max_hp=100, hp=50))
    ally2 = Character(name="Rogue", stats=Stats(base_max_hp=80, hp=30))
    ally3 = Character(name="Mage", stats=Stats(base_max_hp=60, hp=20))

    # Create AOE heal with max_targets=None (unlimited)
    group_heal = create_heal_skill(
        "Mass Heal", mp_cost=20, heal_amount=25, max_targets=None
    )

    result = group_heal.execute(healer, [ally1, ally2, ally3], {})

    assert result.success
    assert len(result.targets_hit) == 3
    assert ally1.stats.hp == 75
    assert ally2.stats.hp == 55
    assert ally3.stats.hp == 45


def test_attack_range_validation():
    """Attack should fail if target is out of range."""
    from barebones_rpg.items.item import create_weapon

    attacker = Character(
        name="Archer", stats=Stats(strength=15, base_accuracy=100), position=(0, 0)
    )
    target = Enemy(name="Distant Goblin", stats=Stats(hp=50), position=(10, 10))

    # Give attacker a melee weapon (range=1)
    sword = create_weapon("Sword", base_damage=10, range=1)
    attacker.init_equipment()
    attacker.equipment.equip(sword)

    action = AttackAction()
    result = action.execute(attacker, [target], {})

    assert result.success is False
    assert "out of range" in result.message.lower()


def test_attack_succeeds_within_range():
    """Attack should succeed if target is within range."""
    from barebones_rpg.items.item import create_weapon

    attacker = Character(
        name="Archer",
        stats=Stats(strength=15, base_accuracy=100, base_critical=0),
        position=(0, 0),
    )
    target = Enemy(
        name="Close Goblin", stats=Stats(hp=50, constitution=0), position=(3, 0)
    )

    # Give attacker a ranged weapon (range=5)
    bow = create_weapon("Bow", base_damage=8, range=5)
    attacker.init_equipment()
    attacker.equipment.equip(bow)

    action = AttackAction()
    result = action.execute(attacker, [target], {})

    assert result.success is True
    assert result.damage > 0


def test_cleave_attack_hits_limited_targets():
    """Cleave attack should hit only max_targets number of enemies."""
    from barebones_rpg.combat.actions import create_skill_action

    attacker = Character(
        name="Warrior", stats=Stats(strength=20, base_max_mp=30, mp=30)
    )
    enemy1 = Enemy(name="Goblin1", stats=Stats(constitution=0, hp=30))
    enemy2 = Enemy(name="Goblin2", stats=Stats(constitution=0, hp=30))
    enemy3 = Enemy(name="Goblin3", stats=Stats(constitution=0, hp=30))
    enemy4 = Enemy(name="Goblin4", stats=Stats(constitution=0, hp=30))

    # Create cleave skill that hits 2 targets
    cleave = create_skill_action(
        "Cleave",
        mp_cost=10,
        damage_multiplier=1.0,
        damage_type="physical",
        max_targets=2,
    )

    result = cleave.execute(attacker, [enemy1, enemy2, enemy3, enemy4], {})

    assert result.success
    assert len(result.targets_hit) == 2  # Only hits first 2
    assert enemy1 in result.targets_hit
    assert enemy2 in result.targets_hit
    assert enemy3 not in result.targets_hit
    assert enemy4 not in result.targets_hit
    assert enemy1.stats.hp < 30
    assert enemy2.stats.hp < 30
    assert enemy3.stats.hp == 30  # Not hit
    assert enemy4.stats.hp == 30  # Not hit


def test_aoe_damage_handles_individual_deaths():
    """AOE damage should properly handle when only some targets die."""
    from barebones_rpg.combat.actions import create_skill_action

    caster = Character(
        name="Mage",
        stats=Stats(intelligence=15, base_accuracy=100, base_max_mp=50, mp=50),
    )

    # One enemy with full HP, one with 1 HP
    full_hp_enemy = Enemy(
        name="Healthy Goblin", stats=Stats(constitution=0, hp=50, base_max_hp=50)
    )
    low_hp_enemy = Enemy(
        name="Wounded Goblin", stats=Stats(constitution=0, hp=1, base_max_hp=50)
    )

    # Create AOE skill with max_targets=None
    fireball = create_skill_action(
        "Fireball",
        mp_cost=10,
        damage_multiplier=1.0,
        damage_type="magic",
        max_targets=None,
    )

    result = fireball.execute(caster, [full_hp_enemy, low_hp_enemy], {})

    assert result.success
    assert len(result.targets_hit) == 2

    # Both should have been hit
    assert full_hp_enemy in result.targets_hit
    assert low_hp_enemy in result.targets_hit

    # Low HP enemy should be dead
    assert low_hp_enemy.is_dead()
    assert low_hp_enemy.stats.hp == 0

    # Full HP enemy should be damaged but alive
    assert full_hp_enemy.is_alive()
    assert full_hp_enemy.stats.hp < 50
    assert full_hp_enemy.stats.hp > 0

    # Total damage should be sum of both
    assert result.damage > 0
