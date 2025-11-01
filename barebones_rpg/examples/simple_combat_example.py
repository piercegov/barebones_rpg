"""Simple combat example.

This example demonstrates:
- Creating characters and enemies
- Setting up a combat encounter
- Turn-based combat mechanics
- Event system usage
"""

from barebones_rpg import (
    Game,
    GameConfig,
    Character,
    Enemy,
    Stats,
    Combat,
    create_weapon,
    create_heal_skill,
    AttackAction,
    EventType,
)


def main():
    """Run a simple combat example."""
    print("=== Barebones RPG: Simple Combat Example ===\n")

    # Create game
    config = GameConfig(title="Combat Example", debug_mode=True)
    game = Game(config)

    # Subscribe to combat events
    def on_damage(event):
        result = event.data.get("result")
        if result and result.damage > 0:
            print(f"  💥 {result.message}")

    def on_death(event):
        entity = event.data.get("entity")
        print(f"  ⚰️  {entity.name} has been defeated!")

    game.events.subscribe(EventType.ATTACK, on_damage)
    game.events.subscribe(EventType.DEATH, on_death)

    # Create hero
    hero = Character(
        name="Hero",
        stats=Stats(
            strength=15,
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=50,
            base_max_mp=20,
            hp=100,
            mp=50,
        ),
    )
    hero.init_equipment()

    # Give hero a weapon
    sword = create_weapon("Iron Sword", base_damage=8, damage_type="physical", value=50)
    hero.equipment.equip(sword)
    print(
        f"Hero equipped: {sword.name} ({sword.base_damage} base damage, {sword.damage_type} type)"
    )

    # Create enemies
    goblin1 = Enemy(
        name="Goblin",
        stats=Stats(
            strength=8,
            constitution=6,
            intelligence=5,
            dexterity=12,
            charisma=5,
            base_max_hp=20,
            hp=30,
        ),
        exp_reward=20,
        gold_reward=10,
    )

    goblin2 = Enemy(
        name="Goblin Scout",
        stats=Stats(
            strength=10,
            constitution=5,
            intelligence=5,
            dexterity=16,
            charisma=5,
            base_max_hp=15,
            hp=25,
        ),
        exp_reward=25,
        gold_reward=15,
    )

    print(f"\nEncountered: {goblin1.name} and {goblin2.name}!\n")

    # Create combat
    combat = Combat(
        player_group=[hero], enemy_group=[goblin1, goblin2], events=game.events
    )

    # Add victory callback
    def on_victory(combat_instance):
        print("\n🎉 Victory!")
        total_exp = sum(e.exp_reward for e in combat_instance.enemies.members)
        total_gold = sum(e.gold_reward for e in combat_instance.enemies.members)
        print(f"Gained {total_exp} EXP and {total_gold} gold!")

    combat.on_victory(on_victory)

    # Start combat
    combat.start()

    # Simulate combat turns
    turn = 1
    while combat.is_active():
        current = combat.get_current_combatant()
        if not current:
            break

        print(f"\n--- Turn {turn}: {current.name}'s turn ---")
        print(f"HP: {current.stats.hp}/{current.stats.get_max_hp()}")

        if current == hero:
            # Player's turn - attack first enemy
            alive_enemies = combat.enemies.get_alive_members()
            if alive_enemies:
                target = alive_enemies[0]
                print(f"Hero attacks {target.name}!")
                action = AttackAction()
                combat.execute_action(action, hero, [target])

                # Check if combat ended
                if not combat.is_active():
                    break

                combat.end_turn()
        else:
            # Enemy turn (handled automatically by end_turn)
            pass

        turn += 1

        # Safety check
        if turn > 50:
            print("Combat took too long, ending...")
            break

    print("\nCombat ended!")
    print(f"Final hero HP: {hero.stats.hp}/{hero.stats.get_max_hp()}")


if __name__ == "__main__":
    main()
