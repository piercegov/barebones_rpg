"""Tests for the combat system."""

import pytest
from barebones_rpg.combat.combat import Combat, CombatState, TurnOrder, CombatantGroup
from barebones_rpg.combat.actions import AttackAction
from barebones_rpg.entities.entity import Character, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.core.events import EventManager, EventType


@pytest.fixture
def combat_setup():
    """Setup a basic combat scenario."""
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=15,
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            hp=100,
        ),
    )
    enemy1 = Enemy(
        name="Goblin",
        stats=Stats(
            strength=8,
            constitution=6,
            intelligence=5,
            dexterity=10,
            charisma=5,
            base_max_hp=20,
            hp=30,
        ),
    )
    enemy2 = Enemy(
        name="Orc",
        stats=Stats(
            strength=12,
            constitution=10,
            intelligence=5,
            dexterity=8,
            charisma=5,
            base_max_hp=30,
            hp=50,
        ),
    )
    events = EventManager()

    combat = Combat([hero], [enemy1, enemy2], events)
    return combat, hero, enemy1, enemy2, events


def test_turn_order_skips_dead_combatants(combat_setup):
    """TurnOrder should automatically skip dead combatants."""
    combat, hero, enemy1, enemy2, events = combat_setup
    combat.start()

    enemy1.stats.hp = 0

    turn_order = combat.turn_order
    alive = turn_order.get_alive_combatants()

    assert enemy1 not in alive
    assert hero in alive
    assert enemy2 in alive


def test_turn_order_wraps_around():
    """Turn order should wrap around at the end of combatants list."""
    hero = Character(name="Hero", stats=Stats(dexterity=12))
    enemy = Enemy(name="Goblin", stats=Stats(dexterity=10))

    turn_order = TurnOrder()
    turn_order.initialize([hero, enemy])

    assert turn_order.get_current() == hero

    turn_order.next_turn()
    assert turn_order.get_current() == enemy

    turn_order.next_turn()
    assert turn_order.get_current() == hero


def test_combat_ends_with_victory(combat_setup):
    """Combat should end with VICTORY when all enemies are dead."""
    combat, hero, enemy1, enemy2, events = combat_setup
    combat.start()

    enemy1.stats.hp = 0
    enemy2.stats.hp = 0

    combat._check_combat_end()

    assert combat.state == CombatState.VICTORY


def test_combat_ends_with_defeat(combat_setup):
    """Combat should end with DEFEAT when all players are dead."""
    combat, hero, enemy1, enemy2, events = combat_setup
    combat.start()

    hero.stats.hp = 0

    combat._check_combat_end()

    assert combat.state == CombatState.DEFEAT


def test_combat_start_event_published(combat_setup):
    """Combat should publish COMBAT_START event when started."""
    combat, hero, enemy1, enemy2, events = combat_setup
    events.enable_history()

    combat.start()

    history = events.get_history()
    start_events = [e for e in history if e.event_type == EventType.COMBAT_START]

    assert len(start_events) == 1


def test_turn_start_event_published(combat_setup):
    """Combat should publish COMBAT_TURN_START event at turn start."""
    combat, hero, enemy1, enemy2, events = combat_setup
    events.enable_history()

    combat.start()

    history = events.get_history()
    turn_start_events = [
        e for e in history if e.event_type == EventType.COMBAT_TURN_START
    ]

    assert len(turn_start_events) >= 1


def test_death_event_published(combat_setup):
    """Combat should publish DEATH event when an entity dies."""
    combat, hero, enemy1, enemy2, events = combat_setup
    events.enable_history()

    combat.start()

    action = AttackAction()
    enemy1.stats.hp = 1
    result = combat.execute_action(action, hero, enemy1)

    history = events.get_history()
    death_events = [e for e in history if e.event_type == EventType.DEATH]

    if enemy1.is_dead():
        assert len(death_events) >= 1


def test_combat_end_event_published(combat_setup):
    """Combat should publish COMBAT_END event when combat ends."""
    combat, hero, enemy1, enemy2, events = combat_setup
    events.enable_history()

    combat.start()

    enemy1.stats.hp = 0
    enemy2.stats.hp = 0
    combat._check_combat_end()

    history = events.get_history()
    end_events = [e for e in history if e.event_type == EventType.COMBAT_END]

    assert len(end_events) == 1
    assert end_events[0].data["result"] == "VICTORY"


def test_status_effects_processed_each_turn():
    """Status effects should be processed for all combatants each turn."""
    from barebones_rpg.entities.stats import StatusEffect

    hero = Character(name="Hero", stats=Stats(hp=100, dexterity=12))
    enemy = Enemy(name="Goblin", stats=Stats(hp=30, dexterity=10))

    poison_ticks = {"count": 0}

    def poison_on_turn(stats):
        poison_ticks["count"] += 1

    poison = StatusEffect(name="Poison", duration=2, on_turn=poison_on_turn)
    hero.stats_manager.add_status_effect(poison)

    combat = Combat([hero], [enemy], EventManager())
    combat.start()

    assert poison_ticks["count"] == 1


def test_combatant_group_is_defeated():
    """CombatantGroup should be defeated when all members are dead."""
    hero1 = Character(name="Hero1", stats=Stats(hp=0))
    hero2 = Character(name="Hero2", stats=Stats(hp=0))

    group = CombatantGroup(name="Heroes", members=[hero1, hero2])

    assert group.is_defeated()


def test_combatant_group_not_defeated():
    """CombatantGroup should not be defeated when at least one member is alive."""
    hero1 = Character(name="Hero1", stats=Stats(hp=100))
    hero2 = Character(name="Hero2", stats=Stats(hp=0))

    group = CombatantGroup(name="Heroes", members=[hero1, hero2])

    assert not group.is_defeated()


def test_turn_order_initialized_by_speed():
    """Turn order should be sorted by speed (highest first)."""
    slow = Character(name="Slow", stats=Stats(dexterity=8))
    medium = Character(name="Medium", stats=Stats(dexterity=12))
    fast = Character(name="Fast", stats=Stats(dexterity=16))

    turn_order = TurnOrder()
    turn_order.initialize([slow, medium, fast])

    assert turn_order.combatants[0] == fast
    assert turn_order.combatants[1] == medium
    assert turn_order.combatants[2] == slow


def test_combat_is_active():
    """Combat should be active during player and enemy turns."""
    hero = Character(name="Hero", stats=Stats(dexterity=12))
    enemy = Enemy(name="Goblin", stats=Stats(dexterity=10))

    combat = Combat([hero], [enemy], EventManager())

    assert not combat.is_active()

    combat.start()

    assert combat.is_active()


def test_victory_callback_executed():
    """Victory callback should be executed when combat is won."""
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=20,
            constitution=15,
            intelligence=10,
            dexterity=12,
            charisma=10,
            hp=100,
        ),
    )
    hero.init_equipment()  # Initialize equipment so AttackAction works properly
    enemy = Enemy(
        name="Goblin",
        stats=Stats(
            strength=5, constitution=3, intelligence=5, dexterity=10, charisma=5, hp=1
        ),
    )

    combat = Combat([hero], [enemy], EventManager())

    victory_called = {"called": False}

    def on_victory(combat):
        victory_called["called"] = True

    combat.on_victory(on_victory)
    combat.start()

    action = AttackAction()
    combat.execute_action(action, hero, enemy)

    assert victory_called["called"]
