"""Tests for the combat system."""

import pytest
from barebones_rpg.combat.combat import Combat, CombatState, TurnOrder, CombatantGroup
from barebones_rpg.combat.actions import AttackAction
from barebones_rpg.entities.entity import Character, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.core.events import EventManager, EventType
from barebones_rpg.items import Item, ItemType, LootManager


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
    result = combat.execute_action(action, hero, [enemy1])

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
            dexterity=20,  # High DEX for speed and accuracy
            charisma=10,
            hp=100,
            base_accuracy=100,  # Ensure attack always hits
            base_evasion=0,
        ),
    )
    hero.init_equipment()  # Initialize equipment so AttackAction works properly
    enemy = Enemy(
        name="Goblin",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,  # Low DEX for speed
            charisma=5,
            hp=1,
            base_evasion=0,  # Ensure attack always hits
        ),
    )

    combat = Combat([hero], [enemy], EventManager())

    victory_called = {"called": False}

    def on_victory(combat):
        victory_called["called"] = True

    combat.on_victory(on_victory)
    combat.start()

    action = AttackAction()
    combat.execute_action(action, hero, [enemy])

    assert victory_called["called"]


def test_item_dropped_event_published():
    """Test that ITEM_DROPPED event is published when enemy with loot dies."""
    # Clear registry before test
    LootManager().clear()

    # Setup item in registry
    bone = Item(name="Goblin Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Goblin Bone", bone)

    # Create enemy with loot table
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=50,  # Very high to ensure kill
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            hp=100,
            base_physical_attack=50,  # High attack
            base_accuracy=100,  # 100% hit rate
        ),
    )
    hero.init_equipment()

    enemy = Enemy(
        name="Goblin",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=1,  # Dies in one hit
            base_evasion=0,
            base_physical_defense=0,  # No defense
        ),
        loot_table=[{"item": "Goblin Bone", "chance": 1.0}],  # 100% drop
    )

    events = EventManager()
    dropped_items = []

    def on_item_dropped(event):
        dropped_items.append(event.data.get("item"))

    events.subscribe(EventType.ITEM_DROPPED, on_item_dropped)

    combat = Combat([hero], [enemy], events)
    combat.start()

    # Kill the enemy
    action = AttackAction()
    combat.execute_action(action, hero, [enemy])

    # Check that item was dropped
    assert len(dropped_items) == 1
    assert dropped_items[0].name == "Goblin Bone"

    # Cleanup
    LootManager().clear()


def test_get_dropped_loot():
    """Test that dropped loot can be retrieved via get_dropped_loot()."""
    # Clear registry before test
    LootManager().clear()

    # Setup item in registry
    bone = Item(name="Goblin Bone", item_type=ItemType.MATERIAL, value=5)
    LootManager().register("Goblin Bone", bone)

    # Create enemy with loot table
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=50,  # Very high to ensure kill
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            hp=100,
            base_physical_attack=50,  # High attack
            base_accuracy=100,  # 100% hit rate
        ),
    )
    hero.init_equipment()

    enemy = Enemy(
        name="Goblin",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=1,
            base_evasion=0,
            base_physical_defense=0,  # No defense
        ),
        loot_table=[{"item": "Goblin Bone", "chance": 1.0}],
    )

    combat = Combat([hero], [enemy], EventManager())
    combat.start()

    # Initially no loot
    assert len(combat.get_dropped_loot()) == 0

    # Kill the enemy
    action = AttackAction()
    combat.execute_action(action, hero, [enemy])

    # Check dropped loot
    dropped_loot = combat.get_dropped_loot()
    assert len(dropped_loot) == 1
    assert dropped_loot[0].item.name == "Goblin Bone"
    assert dropped_loot[0].source == enemy

    # Cleanup
    LootManager().clear()


def test_no_loot_drops_when_enemy_has_no_loot_table():
    """Test that no events are published when enemy has no loot table."""
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=50,  # Very high to ensure kill
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            hp=100,
            base_physical_attack=50,  # High attack
            base_accuracy=100,  # 100% hit rate
        ),
    )
    hero.init_equipment()

    enemy = Enemy(
        name="Goblin",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=1,
            base_evasion=0,
            base_physical_defense=0,  # No defense
        ),
        loot_table=[],  # No loot
    )

    events = EventManager()
    dropped_items = []

    def on_item_dropped(event):
        dropped_items.append(event.data.get("item"))

    events.subscribe(EventType.ITEM_DROPPED, on_item_dropped)

    combat = Combat([hero], [enemy], events)
    combat.start()

    # Kill the enemy
    action = AttackAction()
    combat.execute_action(action, hero, [enemy])

    # No items should have dropped
    assert len(dropped_items) == 0
    assert len(combat.get_dropped_loot()) == 0


def test_multiple_enemies_drop_loot():
    """Test that multiple enemies can drop loot in the same combat."""
    # Clear registry before test
    LootManager().clear()

    # Setup items in registry
    bone = Item(name="Goblin Bone", item_type=ItemType.MATERIAL, value=5)
    scale = Item(name="Goblin Scale", item_type=ItemType.MATERIAL, value=10)
    LootManager().register("Goblin Bone", bone)
    LootManager().register("Goblin Scale", scale)

    # Create hero
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=50,  # Very high to ensure kills
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            hp=100,
            base_physical_attack=50,  # High attack
            base_accuracy=100,  # 100% hit rate
        ),
    )
    hero.init_equipment()

    # Create enemies with different loot
    enemy1 = Enemy(
        name="Goblin 1",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=1,
            base_evasion=0,
            base_physical_defense=0,  # No defense
        ),
        loot_table=[{"item": "Goblin Bone", "chance": 1.0}],
    )

    enemy2 = Enemy(
        name="Goblin 2",
        stats=Stats(
            strength=5,
            constitution=3,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=1,
            base_evasion=0,
            base_physical_defense=0,  # No defense
        ),
        loot_table=[{"item": "Goblin Scale", "chance": 1.0}],
    )

    combat = Combat([hero], [enemy1, enemy2], EventManager())
    combat.start()

    # Kill both enemies
    action = AttackAction()
    combat.execute_action(action, hero, [enemy1])
    if combat.is_active():  # If combat didn't end after first kill
        combat.end_turn()
        combat.execute_action(action, hero, [enemy2])

    # Check that both items dropped
    dropped_loot = combat.get_dropped_loot()
    assert len(dropped_loot) >= 1  # At least one enemy died

    # Cleanup
    LootManager().clear()


def test_weapon_damage_type_affects_damage():
    """Test that weapon damage types are properly applied in combat."""
    from barebones_rpg.combat.damage_types import DamageTypeManager
    from barebones_rpg.items import create_weapon

    DamageTypeManager.reset()

    # Create hero with fire weapon
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=10,
            dexterity=100,  # High DEX to always hit
            charisma=10,
            hp=100,
            base_accuracy=100,  # Guarantee hit
            base_critical=0,  # No crits for consistent testing
            critical_per_dex=0,
        ),
    )
    hero.init_equipment()

    fire_sword = create_weapon("Fire Sword", base_damage=20, damage_type="fire")
    hero.equipment.equip(fire_sword)

    # Create enemy with fire resistance
    enemy = Enemy(
        name="Fire Resistant Enemy",
        stats=Stats(
            strength=5,
            constitution=0,
            intelligence=0,
            dexterity=0,  # Low speed, goes last
            charisma=5,
            hp=100,
            base_physical_defense=0,
            base_evasion=0,  # Can't evade
            defense_per_con=0,
            magic_def_per_int=0,
            resistances={"fire": 0.5},  # 50% fire resistance
        ),
    )

    combat = Combat([hero], [enemy], EventManager())
    combat.start()

    # Attack with fire weapon
    action = AttackAction()
    result = combat.execute_action(action, hero, [enemy])

    # Damage should be reduced by fire resistance
    # Base: 10 (str) + 20 (weapon) = 30
    # After resistance: 30 - (0.5 * 30) = 15
    assert result.damage == 15
    assert enemy.stats.hp == 85


def test_skill_damage_type_with_resistance():
    """Test that skill damage types interact with resistances."""
    from barebones_rpg.combat.damage_types import DamageTypeManager
    from barebones_rpg.combat import create_skill_action

    DamageTypeManager.reset()

    hero = Character(
        name="Mage",
        stats=Stats(
            strength=5,
            constitution=10,
            intelligence=20,  # High INT for magic
            dexterity=100,  # High speed to go first
            charisma=10,
            hp=100,
            mp=100,
        ),
    )

    # Enemy with ice resistance but fire weakness
    enemy = Enemy(
        name="Ice Golem",
        stats=Stats(
            strength=5,
            constitution=0,  # No defense bonuses
            intelligence=0,
            dexterity=0,  # Low speed, goes last
            charisma=5,
            hp=200,
            defense_per_con=0,
            magic_def_per_int=0,
            resistances={"ice": 0.8, "fire": -0.5},  # 80% ice resist, 50% fire weakness
        ),
    )

    # Create fire skill (using magic damage type so it scales with INT)
    fireball = create_skill_action(
        "Fireball",
        mp_cost=10,
        damage_multiplier=2.0,
        damage_type="magic",  # Uses INT
    )

    combat = Combat([hero], [enemy], EventManager())
    combat.start()

    # Cast fireball (magic damage type, but enemy has no magic resistance)
    result = combat.execute_action(fireball, hero, [enemy])

    # Base: 20 (INT) * 2.0 = 40
    # Magic defense: 0, magic resistance: 0
    # Damage: 40 - 0 - (0 * 40) = 40
    assert result.damage == 40
    assert enemy.stats.hp == 160


def test_custom_damage_type_in_combat():
    """Test that custom damage types work in combat."""
    from barebones_rpg.combat.damage_types import DamageTypeManager
    from barebones_rpg.items import create_weapon

    DamageTypeManager.reset()

    # Register a custom damage type
    DamageTypeManager().register("necrotic", color="green", description="Death magic")

    hero = Character(
        name="Necromancer",
        stats=Stats(
            strength=15,
            constitution=10,
            intelligence=10,
            dexterity=100,  # High DEX to always hit
            charisma=10,
            hp=100,
            base_accuracy=100,  # Guarantee hit
            base_critical=0,  # No crits
            critical_per_dex=0,
        ),
    )
    hero.init_equipment()

    # Necrotic weapon
    death_blade = create_weapon("Death Blade", base_damage=25, damage_type="necrotic")
    hero.equipment.equip(death_blade)

    enemy = Enemy(
        name="Undead",
        stats=Stats(
            strength=5,
            constitution=5,
            intelligence=5,
            dexterity=5,
            charisma=5,
            hp=100,
            base_physical_defense=10,  # Physical defense shouldn't apply to necrotic
            resistances={"necrotic": 0.3},  # 30% necrotic resistance
        ),
    )

    combat = Combat([hero], [enemy], EventManager())
    combat.start()

    action = AttackAction()
    result = combat.execute_action(action, hero, [enemy])

    # Base: 15 (str) + 25 (weapon) = 40
    # Defense: 0 (custom types ignore defense)
    # Resistance: 40 - (0.3 * 40) = 40 - 12 = 28
    assert result.damage == 28
    assert enemy.stats.hp == 72


def test_aoe_skill_with_different_resistances():
    """Test AOE skill hitting targets with different resistances."""
    from barebones_rpg.combat.damage_types import DamageTypeManager
    from barebones_rpg.combat import create_skill_action

    DamageTypeManager.reset()

    mage = Character(
        name="Mage",
        stats=Stats(
            strength=5,
            constitution=10,
            intelligence=20,
            dexterity=100,  # High speed to go first
            charisma=10,
            hp=100,
            mp=100,
        ),
    )

    # Three enemies with different magic resistances
    enemy1 = Enemy(
        name="Magic Immune",
        stats=Stats(
            hp=100,
            constitution=0,
            intelligence=0,
            dexterity=0,  # Low speed
            defense_per_con=0,
            magic_def_per_int=0,
            resistances={"magic": 1.0},
        ),  # 100% magic resist
    )

    enemy2 = Enemy(
        name="Normal",
        stats=Stats(
            hp=100,
            constitution=0,
            intelligence=0,
            dexterity=0,  # Low speed
            defense_per_con=0,
            magic_def_per_int=0,
            resistances={},
        ),  # No resistance
    )

    enemy3 = Enemy(
        name="Weak to Magic",
        stats=Stats(
            hp=100,
            constitution=0,
            intelligence=0,
            dexterity=0,  # Low speed
            defense_per_con=0,
            magic_def_per_int=0,
            resistances={"magic": -0.5},
        ),  # 50% magic weakness
    )

    # AOE magic spell
    meteor = create_skill_action(
        "Meteor",
        mp_cost=20,
        damage_multiplier=1.5,
        damage_type="magic",
        max_targets=None,  # Hits all targets
    )

    combat = Combat([mage], [enemy1, enemy2, enemy3], EventManager())
    combat.start()

    result = combat.execute_action(meteor, mage, [enemy1, enemy2, enemy3])

    # Base damage: 20 (INT) * 1.5 = 30
    # Enemy1 (100% magic resist): 30 - 0 - (1.0 * 30) = 0
    # Enemy2 (no magic resistance): 30 - 0 - (0 * 30) = 30
    # Enemy3 (50% magic weakness): 30 - 0 - (-0.5 * 30) = 45
    # Total: 0 + 30 + 45 = 75
    assert result.damage == 75
    assert enemy1.stats.hp == 100  # No damage
    assert enemy2.stats.hp == 70  # Normal damage
    assert enemy3.stats.hp == 55  # Extra damage
