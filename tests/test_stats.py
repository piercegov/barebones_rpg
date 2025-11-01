"""Tests for the stats system."""

import pytest
from barebones_rpg.entities.stats import Stats, StatusEffect, StatsManager


def test_restore_hp_caps_at_max(basic_stats):
    """HP restoration should cap at max_hp and return actual amount restored."""
    basic_stats.hp = 50
    actual_restored = basic_stats.restore_hp(100)

    assert basic_stats.hp == 100
    assert actual_restored == 50


def test_restore_mp_caps_at_max(basic_stats):
    """MP restoration should cap at max_mp and return actual amount restored."""
    basic_stats.mp = 20
    actual_restored = basic_stats.restore_mp(100)

    assert basic_stats.mp == 50
    assert actual_restored == 30


def test_damage_floors_at_zero(basic_stats):
    """Damage should floor at 0 HP, not go negative."""
    actual_damage = basic_stats.take_damage(150)

    assert basic_stats.hp == 0
    assert actual_damage == 100


def test_is_alive_and_is_dead(basic_stats):
    """is_alive and is_dead should correctly reflect HP status."""
    assert basic_stats.is_alive()
    assert not basic_stats.is_dead()

    basic_stats.take_damage(100)

    assert not basic_stats.is_alive()
    assert basic_stats.is_dead()


def test_multiple_status_effect_modifiers_stack():
    """Multiple status effects should stack their stat modifiers correctly."""
    stats = Stats(strength=10, constitution=10)
    manager = StatsManager(stats)

    effect1 = StatusEffect(
        name="Buff1", stat_modifiers={"strength": 5, "constitution": 2}
    )
    effect2 = StatusEffect(
        name="Buff2", stat_modifiers={"strength": 3, "constitution": 1}
    )

    manager.add_status_effect(effect1)
    manager.add_status_effect(effect2)

    assert manager.get_effective_stat("strength") == 18
    assert manager.get_effective_stat("constitution") == 13


def test_status_effect_expiration():
    """Temporary status effects should expire after duration runs out."""
    stats = Stats()
    manager = StatsManager(stats)

    temporary_effect = StatusEffect(
        name="TempBuff", duration=2, stat_modifiers={"strength": 10}
    )
    permanent_effect = StatusEffect(
        name="PermBuff", duration=-1, stat_modifiers={"constitution": 5}
    )

    manager.add_status_effect(temporary_effect)
    manager.add_status_effect(permanent_effect)

    assert manager.has_status("TempBuff")
    assert manager.has_status("PermBuff")

    manager.process_status_effects()
    assert manager.has_status("TempBuff")

    manager.process_status_effects()
    assert not manager.has_status("TempBuff")
    assert manager.has_status("PermBuff")


def test_custom_stats_via_dict():
    """Custom stats should be accessible via the custom dictionary."""
    stats = Stats()

    stats.modify("luck", 15)
    assert stats.get_stat("luck") == 15

    stats.set_stat("charisma", 20)
    assert stats.get_stat("charisma") == 20

    stats.modify("luck", 5)
    assert stats.get_stat("luck") == 20


def test_remove_nonexistent_status_effect():
    """Removing a non-existent status effect should fail gracefully."""
    stats = Stats()
    manager = StatsManager(stats)

    result = manager.remove_status_effect("NonExistent")
    assert result is False


def test_remove_existing_status_effect():
    """Removing an existing status effect should return True and remove it."""
    stats = Stats()
    manager = StatsManager(stats)

    effect = StatusEffect(name="TestEffect", stat_modifiers={"strength": 5})
    manager.add_status_effect(effect)

    assert manager.has_status("TestEffect")

    result = manager.remove_status_effect("TestEffect")
    assert result is True
    assert not manager.has_status("TestEffect")


def test_status_effect_on_turn_callback():
    """Status effects with on_turn callback should execute during processing."""
    stats = Stats(hp=100)
    manager = StatsManager(stats)

    call_count = {"count": 0}

    def poison_effect(stats):
        stats.take_damage(5)
        call_count["count"] += 1

    poison = StatusEffect(name="Poison", duration=3, on_turn=poison_effect)
    manager.add_status_effect(poison)

    manager.process_status_effects()
    assert stats.hp == 95
    assert call_count["count"] == 1

    manager.process_status_effects()
    assert stats.hp == 90
    assert call_count["count"] == 2


def test_stats_modify_on_regular_stat():
    """Modify should work on regular stat fields."""
    stats = Stats(strength=10)
    stats.modify("strength", 5)
    assert stats.strength == 15

    stats.modify("strength", -3)
    assert stats.strength == 12


def test_get_effective_stat_with_no_effects():
    """get_effective_stat should return base value when no effects applied."""
    stats = Stats(strength=15, constitution=10)
    manager = StatsManager(stats)

    assert manager.get_effective_stat("strength") == 15
    assert manager.get_effective_stat("constitution") == 10


def test_get_effective_stat_with_default():
    """get_effective_stat should return default for non-existent stats."""
    stats = Stats()
    manager = StatsManager(stats)

    assert manager.get_effective_stat("nonexistent", default=99) == 99
