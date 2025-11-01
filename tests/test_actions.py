"""Tests for combat actions."""
import pytest
import random
from barebones_rpg.combat.actions import (
    AttackAction, SkillAction, RunAction,
    ActionResult
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
        stats=Stats(hp=100, atk=20, accuracy=90, critical=5, speed=10)
    )
    target = Enemy(
        name="Goblin",
        stats=Stats(hp=50, defense=5, evasion=10, speed=8)
    )
    return attacker, target


def test_attack_with_no_target_returns_failure():
    """Attack with no target should return failure."""
    attacker = Character(name="Hero", stats=Stats(atk=15))
    action = AttackAction()
    
    result = action.execute(attacker, None, {})
    
    assert result.success is False
    assert result.message == "No target selected"


def test_attack_misses_based_on_accuracy(attacker_and_target, monkeypatch):
    """Attack should miss based on accuracy/evasion calculation."""
    attacker, target = attacker_and_target
    action = AttackAction()
    
    def always_miss(a, b):
        return 100
    
    monkeypatch.setattr(random, "randint", always_miss)
    
    result = action.execute(attacker, target, {})
    
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
    result = action.execute(attacker, target, {})
    
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
    
    result = action.execute(attacker, target, {})
    
    assert result.critical is True
    assert result.damage > 0


def test_skill_mp_cost_prevents_execution():
    """Skill with insufficient MP should fail to execute."""
    caster = Character(name="Mage", stats=Stats(mp=10, max_mp=50))
    target = Enemy(name="Goblin", stats=Stats(hp=50))
    
    def skill_effect(source, target, context):
        return ActionResult(success=True, damage=30)
    
    skill = SkillAction("Fireball", mp_cost=20, effect=skill_effect)
    
    result = skill.execute(caster, target, {})
    
    assert result.success is False
    assert "doesn't have enough MP" in result.message


def test_skill_executes_with_sufficient_mp():
    """Skill should execute when caster has enough MP."""
    caster = Character(name="Mage", stats=Stats(mp=50, max_mp=50, atk=15))
    target = Enemy(name="Goblin", stats=Stats(hp=50, defense=0))
    
    def skill_effect(source, target, context):
        damage = target.take_damage(30, source)
        return ActionResult(success=True, damage=damage, message="Fireball!")
    
    skill = SkillAction("Fireball", mp_cost=20, effect=skill_effect)
    
    result = skill.execute(caster, target, {})
    
    assert result.success is True
    assert caster.stats.mp == 30
    assert target.stats.hp == 20


def test_run_action_success_rate_with_speed_difference(monkeypatch):
    """Run action success rate should be affected by speed difference."""
    fast_runner = Character(name="Fast", stats=Stats(speed=20))
    slow_enemy = Enemy(name="Slow", stats=Stats(speed=10))
    
    def favorable_roll(a, b):
        return 50
    
    monkeypatch.setattr(random, "randint", favorable_roll)
    
    action = RunAction()
    result = action.execute(fast_runner, slow_enemy, {})
    
    assert result.success is True
    assert result.metadata.get("fled") is True


def test_run_action_fails(monkeypatch):
    """Run action can fail."""
    runner = Character(name="Runner", stats=Stats(speed=10))
    enemy = Enemy(name="Enemy", stats=Stats(speed=10))
    
    def unfavorable_roll(a, b):
        return 100
    
    monkeypatch.setattr(random, "randint", unfavorable_roll)
    
    action = RunAction()
    result = action.execute(runner, enemy, {})
    
    assert result.success is True
    assert result.metadata.get("fled") is False


def test_skill_can_execute_checks_mp():
    """Skill can_execute should check MP availability."""
    low_mp_caster = Character(name="Tired Mage", stats=Stats(mp=5))
    
    def dummy_effect(source, target, context):
        return ActionResult(success=True)
    
    skill = SkillAction("Expensive Spell", mp_cost=20, effect=dummy_effect)
    
    can_execute = skill.can_execute(low_mp_caster, {})
    
    assert can_execute is False


def test_attack_action_calculates_damage_correctly():
    """Attack action should calculate damage as atk - defense with minimum 1."""
    attacker = Character(name="Hero", stats=Stats(atk=15, accuracy=100, critical=0))
    target = Enemy(name="Tank", stats=Stats(hp=100, defense=10, evasion=0))
    
    action = AttackAction()
    result = action.execute(attacker, target, {})
    
    assert result.damage > 1


def test_attack_action_calculates_damage_correctly_atk_lower():
    """Attack action should calculate damage as atk - defense with minimum 1."""
    attacker = Character(name="Hero", stats=Stats(atk=5, accuracy=100, critical=0))
    target = Enemy(name="Tank", stats=Stats(hp=100, defense=10, evasion=0))
    
    action = AttackAction()
    result = action.execute(attacker, target, {})
    
    assert result.damage == 1


def test_skill_action_deducts_mp_cost():
    """SkillAction should deduct MP cost when executed."""
    caster = Character(name="Mage", stats=Stats(mp=50, max_mp=50))
    target = Enemy(name="Goblin", stats=Stats(hp=50))
    
    def skill_effect(source, target, context):
        return ActionResult(success=True, message="Boom!")
    
    skill = SkillAction("Magic Missile", mp_cost=15, effect=skill_effect)
    
    old_mp = caster.stats.mp
    result = skill.execute(caster, target, {})
    
    assert caster.stats.mp == old_mp - 15

