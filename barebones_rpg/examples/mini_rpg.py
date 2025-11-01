"""Mini RPG example.

This example demonstrates:
- Creating a world with locations
- NPCs with dialog trees
- Quest system
- Inventory and items
- Complete game flow
"""

from barebones_rpg import (
    Game,
    GameConfig,
    Character,
    NPC,
    Enemy,
    Stats,
    World,
    Location,
    DialogTree,
    DialogNode,
    DialogChoice,
    DialogSession,
    Quest,
    QuestObjective,
    ObjectiveType,
    QuestManager,
    create_consumable,
    create_weapon,
    Inventory,
)


def create_game_world():
    """Create the game world with locations and NPCs."""
    world = World(name="Tutorial World", description="A simple tutorial world")

    # Create village
    village = Location(
        name="Peaceful Village",
        description="A quiet village surrounded by forests",
        width=30,
        height=30,
    )

    # Create forest
    forest = Location(
        name="Dark Forest",
        description="A dangerous forest full of monsters",
        width=40,
        height=40,
    )

    # Connect locations
    world.add_location(village)
    world.add_location(forest)
    world.connect_locations(village.id, "north", forest.id, bidirectional=True)

    return world, village, forest


def create_elder_dialog():
    """Create dialog tree for the village elder."""
    tree = DialogTree(name="Elder Dialog")

    greeting = DialogNode(
        id="greeting",
        speaker="Village Elder",
        text="Welcome, brave adventurer! Our village needs your help.",
        choices=[
            DialogChoice(text="What's wrong?", next_node_id="problem"),
            DialogChoice(text="I'm just passing through", next_node_id="goodbye"),
        ],
    )

    problem = DialogNode(
        id="problem",
        speaker="Village Elder",
        text="Goblins from the Dark Forest have been raiding our village. Please help us!",
        choices=[
            DialogChoice(text="I'll help!", next_node_id="accept_quest"),
            DialogChoice(text="Sorry, I can't", next_node_id="goodbye"),
        ],
    )

    accept_quest = DialogNode(
        id="accept_quest",
        speaker="Village Elder",
        text="Thank you! Please defeat the goblin chief in the Dark Forest. Take this sword!",
        choices=[
            DialogChoice(text="I won't let you down!", next_node_id=None),
        ],
    )

    goodbye = DialogNode(
        id="goodbye",
        speaker="Village Elder",
        text="Safe travels, adventurer.",
        choices=[],
    )

    tree.add_node(greeting)
    tree.add_node(problem)
    tree.add_node(accept_quest)
    tree.add_node(goodbye)
    tree.set_start_node("greeting")

    return tree


def main():
    """Run the mini RPG example."""
    print("=" * 60)
    print("🎮 BAREBONES RPG: Mini Adventure")
    print("=" * 60)
    print("\nA demonstration of the RPG framework capabilities\n")

    # Create game
    config = GameConfig(title="Mini RPG", debug_mode=False)
    game = Game(config)

    # Create player character
    hero = Character(
        name="Adventurer",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=8,
            dexterity=12,
            charisma=10,
            base_max_hp=50,
            base_max_mp=15,
            hp=100,
            mp=30,
        ),
    )
    hero.init_inventory(max_slots=20)

    print(f"You are {hero.name}, a brave adventurer")
    print(
        f"Stats: STR={hero.stats.strength} CON={hero.stats.constitution} DEX={hero.stats.dexterity}"
    )
    print(
        f"HP={hero.stats.hp}/{hero.stats.get_max_hp()} MP={hero.stats.mp}/{hero.stats.get_max_mp()}\n"
    )

    # Create world
    world, village, forest = create_game_world()
    game.register_system("world", world)

    print(f"📍 Location: {village.name}")
    print(f"   {village.description}\n")

    # Create village elder NPC
    elder_dialog = create_elder_dialog()
    elder = NPC(
        name="Village Elder",
        description="A wise old man who leads the village",
        stats=Stats(
            strength=5, constitution=8, intelligence=12, dexterity=6, charisma=15, hp=50
        ),
    )
    village.add_entity(elder, 15, 15)

    print(f"You see: {elder.name}")
    print(f"   {elder.description}\n")

    # Start dialog with elder
    print("--- Conversation ---")
    session = DialogSession(elder_dialog, context={"player": hero, "game": game})
    session.start()

    # Simulate conversation choices
    choices_made = [0, 0]  # "What's wrong?" then "I'll help!"

    for choice_idx in choices_made:
        current_node = session.get_current_node()
        if current_node:
            print(f'\n{current_node.speaker}: "{current_node.text}"')

            choices = session.get_available_choices()
            if choices:
                print("\nYour choices:")
                for i, choice in enumerate(choices):
                    print(f"  {i+1}. {choice.text}")

                if choice_idx < len(choices):
                    chosen = choices[choice_idx]
                    print(f"\n> You chose: {chosen.text}")

                    # Special: Give sword when quest is accepted
                    if current_node.id == "accept_quest":
                        sword = create_weapon("Steel Sword", atk=8, value=100)
                        hero.inventory.add_item(sword)
                        print(f"\n✨ Received: {sword.name}!")
                        hero.stats.atk += sword.stat_modifiers["atk"]

                    session.make_choice(choice_idx)

    print("\n--- End Conversation ---\n")

    # Create quest
    quest = Quest(
        name="Goblin Threat",
        description="Defeat the goblin chief in the Dark Forest",
        exp_reward=100,
        gold_reward=50,
    )
    quest.add_objective(
        QuestObjective(
            description="Defeat the Goblin Chief",
            objective_type=ObjectiveType.KILL_ENEMY,
            target="Goblin Chief",
            target_count=1,
        )
    )

    quest_manager = QuestManager()
    quest_manager.add_quest(quest)
    quest_manager.start_quest(quest.id, game.events)

    print(f"📜 Quest Started: {quest.name}")
    print(f"   {quest.description}\n")

    # Show inventory
    print("🎒 Inventory:")
    for item in hero.inventory.items:
        print(f"   - {item.name}")
    print()

    # Add a health potion
    potion = create_consumable(
        "Health Potion", on_use=lambda entity, ctx: entity.heal(30), value=20
    )
    hero.inventory.add_item(potion)
    print(f"✨ Found: {potion.name}\n")

    # Travel to forest
    print(f"🚶 Traveling to {forest.name}...")
    world.set_current_location(forest.id, game.events)
    print(f"📍 Location: {forest.name}")
    print(f"   {forest.description}\n")

    # Encounter goblin chief
    goblin_chief = Enemy(
        name="Goblin Chief",
        stats=Stats(
            strength=12,
            constitution=10,
            intelligence=6,
            dexterity=12,
            charisma=8,
            base_max_hp=30,
            hp=50,
        ),
        exp_reward=100,
        gold_reward=50,
    )

    print(f"⚔️  Encountered: {goblin_chief.name}!")
    print(f"   HP: {goblin_chief.stats.hp} STR: {goblin_chief.stats.strength}\n")

    # Simulate combat (simplified)
    print("--- Battle ---")
    battle_turn = 1
    while hero.is_alive() and goblin_chief.is_alive():
        print(f"\nTurn {battle_turn}:")

        # Hero attacks
        damage = max(1, hero.stats.atk - goblin_chief.stats.defense)
        goblin_chief.take_damage(damage)
        print(f"  ⚔️  {hero.name} attacks for {damage} damage!")
        print(
            f"     {goblin_chief.name} HP: {goblin_chief.stats.hp}/{goblin_chief.stats.max_hp}"
        )

        if goblin_chief.is_dead():
            break

        # Goblin attacks
        damage = max(1, goblin_chief.stats.atk - hero.stats.defense)
        hero.take_damage(damage)
        print(f"  💢 {goblin_chief.name} attacks for {damage} damage!")
        print(f"     {hero.name} HP: {hero.stats.hp}/{hero.stats.max_hp}")

        battle_turn += 1

        # Use potion if low health
        if hero.stats.hp < 30 and potion in hero.inventory.items:
            healed = hero.heal(30)
            hero.inventory.remove_item(potion)
            print(f"  🧪 Used Health Potion! Healed {healed} HP")

    print("\n--- End Battle ---\n")

    if hero.is_alive():
        print("🎉 Victory!")
        print(f"   Defeated {goblin_chief.name}!")

        # Complete quest
        quest_manager.update_objective(
            quest.id, ObjectiveType.KILL_ENEMY, "Goblin Chief", 1, game.events
        )

        if quest.is_completed():
            print(f"\n✅ Quest Completed: {quest.name}")
            print(f"   Rewards: {quest.exp_reward} EXP, {quest.gold_reward} gold")

            hero.gain_exp(quest.exp_reward, game.events)
            hero.inventory.add_gold(quest.gold_reward)

            print(f"\n📊 Final Stats:")
            print(f"   Level: {hero.stats.level}")
            print(f"   HP: {hero.stats.hp}/{hero.stats.max_hp}")
            print(f"   Gold: {hero.inventory.gold}")
    else:
        print("💀 Defeat...")
        print("   Game Over")

    print("\n" + "=" * 60)
    print("Thanks for playing!")
    print("=" * 60)


if __name__ == "__main__":
    main()
