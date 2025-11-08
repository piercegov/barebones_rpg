"""Example demonstrating the save/load system.

This example shows how to:
- Configure save directory
- Use LootManager for automatic callback registration
- Save and load game state
- Manage multiple save files
"""

from barebones_rpg.core import Game, GameConfig
from barebones_rpg.entities import Character, Enemy, Stats
from barebones_rpg.items import (
    create_weapon,
    create_consumable,
    create_armor,
    LootManager,
)
from barebones_rpg.party import Party
from barebones_rpg.quests import Quest, QuestObjective, ObjectiveType, QuestManager


# Define callbacks that will be used in items/quests
def heal_potion(entity, context):
    """Heal entity by 50 HP."""
    healed = entity.heal(50)
    print(f"{entity.name} healed for {healed} HP!")
    return healed


def mana_potion(entity, context):
    """Restore entity MP by 30."""
    restored = entity.restore_mana(30)
    print(f"{entity.name} restored {restored} MP!")
    return restored


def quest_complete_callback(quest):
    """Called when quest is completed."""
    print(
        f"Quest '{quest.name}' completed! Gained {quest.exp_reward} EXP and {quest.gold_reward} gold!"
    )


def main():
    """Run the save/load example."""
    print("=== Barebones RPG Save/Load Example ===\n")

    # Step 1: Register items with LootManager (auto-registers callbacks!)
    print("1. Registering items with LootManager...")
    health_pot = create_consumable("Health Potion", on_use=heal_potion, value=20)
    mana_pot = create_consumable("Mana Potion", on_use=mana_potion, value=15)

    # When you register items, callbacks are automatically registered
    LootManager().register("health_potion", health_pot)
    LootManager().register("mana_potion", mana_pot)
    print("   ✓ Items registered (callbacks auto-registered!)\n")

    # Step 2: Create game with custom save directory
    print("2. Creating game with custom save directory...")
    config = GameConfig(
        title="Save/Load Demo", save_directory="demo_saves"  # Custom save directory
    )
    game = Game(config)
    print(f"   Save directory: {game.save_manager.save_directory}\n")

    # Step 3: Create and register game entities
    print("3. Creating game world...")

    # Create hero
    hero = Character(
        name="Hero",
        stats=Stats(hp=100, max_hp=100, mp=50, max_mp=50, atk=15, defense=5, level=1),
    )
    hero.init_inventory()
    hero.inventory.add_gold(500)

    # Add items to hero's inventory (get from LootManager)
    hero.inventory.add_item(create_weapon("Iron Sword", base_damage=10, value=50))
    hero.inventory.add_item(create_armor("Leather Armor", defense=5, value=30))
    hero.inventory.add_item(LootManager().get("health_potion"))
    hero.inventory.add_item(LootManager().get("mana_potion"))

    # Register hero
    game.register_entity(hero)
    print(f"   Created hero: {hero.name} (Level {hero.stats.level})")
    print(
        f"   Inventory: {len(hero.inventory.items)} items, {hero.inventory.gold} gold"
    )

    # Create party
    party = Party(name="Adventurers")
    party.add_member(hero)
    party.metadata["formation"] = "offensive"
    game.register_party(party)
    print(f"   Created party: {party.name} with {party.size()} members")

    # Create quest and add to QuestManager (auto-registers callbacks!)
    quest = Quest(
        name="Goblin Extermination",
        description="Clear the goblin camp",
        exp_reward=100,
        gold_reward=50,
        on_complete=quest_complete_callback,
    )
    quest.add_objective(
        QuestObjective(
            description="Defeat 5 goblins",
            objective_type=ObjectiveType.KILL_ENEMY,
            target="Goblin",
            target_count=5,
            current_count=2,  # Already killed 2
        )
    )
    # Add to QuestManager - this auto-registers callbacks
    QuestManager().add_quest(quest)
    game.register_quest(quest)
    print(
        f"   Created quest: {quest.name} ({quest.get_progress_percentage()*100:.0f}% complete)\n"
    )

    # Step 4: Set some game state
    game.clock_time = 123.45
    game.data["current_location"] = "Village"
    game.data["difficulty"] = "Normal"

    # Step 5: Save the game
    print("4. Saving game...")
    success = game.save_to_file("demo_save")
    if success:
        print("   ✓ Game saved successfully!\n")
    else:
        print("   ✗ Failed to save game\n")
        return

    # Step 6: Modify game state (simulate playing)
    print("5. Simulating gameplay...")
    hero.stats.hp = 75  # Take damage
    hero.inventory.remove_gold(100)  # Spend gold
    print(f"   Hero HP: {hero.stats.hp}/{hero.stats.max_hp}")
    print(f"   Gold: {hero.inventory.gold}\n")

    # Step 7: Create another save
    print("6. Creating second save...")
    game.save_to_file("demo_save_2")
    print("   ✓ Second save created\n")

    # Step 8: List all saves
    print("7. Listing all saves...")
    saves = game.list_saves()
    for save_name in saves:
        info = game.save_manager.get_save_info(save_name)
        print(f"   - {save_name}")
        print(f"     Timestamp: {info['timestamp']}")
        print(f"     Size: {info['file_size']} bytes")
    print()

    # Step 9: Load the first save
    print("8. Loading first save...")
    success = game.load_from_file("demo_save")
    if success:
        print("   ✓ Game loaded successfully!")

        # Verify loaded state
        loaded_hero = game.get_entity(hero.id)
        if loaded_hero:
            print(f"   Hero HP: {loaded_hero.stats.hp}/{loaded_hero.stats.max_hp}")
            print(f"   Gold: {loaded_hero.inventory.gold}")
            print(f"   Inventory items: {len(loaded_hero.inventory.items)}")

        loaded_party = game.get_party("Adventurers")
        if loaded_party:
            print(f"   Party: {loaded_party.name} with {loaded_party.size()} members")

        loaded_quest = game.get_quest(quest.id)
        if loaded_quest:
            print(
                f"   Quest: {loaded_quest.name} ({loaded_quest.get_progress_percentage()*100:.0f}% complete)"
            )

        print(f"   Game time: {game.clock_time:.2f}s")
        print(f"   Location: {game.data.get('current_location')}")
    else:
        print("   ✗ Failed to load game")
    print()

    # Step 10: Test callback restoration
    print("9. Testing callback restoration...")
    loaded_hero = game.get_entity(hero.id)
    if loaded_hero and loaded_hero.inventory:
        health_potion = loaded_hero.inventory.find_item("Health Potion")
        if health_potion and health_potion.on_use:
            print(
                f"   Found Health Potion with callback: {health_potion.on_use.__name__}"
            )
            print("   Testing potion use...")
            loaded_hero.stats.hp = 60  # Damage hero
            print(f"   HP before: {loaded_hero.stats.hp}")
            health_potion.use(loaded_hero, {})
            print(f"   HP after: {loaded_hero.stats.hp}")
        else:
            print("   ✗ Health Potion callback not restored")
    print()

    # Step 11: Clean up (optional)
    print("10. Cleaning up demo saves...")
    game.delete_save("demo_save")
    game.delete_save("demo_save_2")
    print("   ✓ Demo saves deleted\n")

    print("=== Example Complete ===")
    print("\nKey Takeaways:")
    print("1. Register items with LootManager - callbacks are auto-registered!")
    print("2. Add quests to QuestManager - callbacks are auto-registered!")
    print("3. Configure save_directory in GameConfig")
    print("4. Register entities, parties, and quests with game.register_*()")
    print("5. Use game.save_to_file() and game.load_from_file() for persistence")
    print("6. Callbacks are automatically serialized and restored")


if __name__ == "__main__":
    main()
