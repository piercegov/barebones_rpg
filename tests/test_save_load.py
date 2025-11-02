"""Tests for save/load system and callback serialization."""

import pytest
import tempfile
import shutil
from pathlib import Path

from barebones_rpg.core import (
    Game,
    GameConfig,
    CallbackRegistry,
    SaveManager,
)
from barebones_rpg.entities import Character, Enemy, Stats
from barebones_rpg.items import (
    Item,
    ItemType,
    create_consumable,
    create_weapon,
    Inventory,
)
from barebones_rpg.party import Party
from barebones_rpg.quests import Quest, QuestObjective, ObjectiveType, QuestStatus


class TestCallbackRegistry:
    """Test callback registry functionality."""

    def setup_method(self):
        """Clear registry before each test."""
        CallbackRegistry.clear()

    def test_register_and_get(self):
        """Test registering and retrieving callbacks."""

        def my_callback():
            return "test"

        CallbackRegistry.register("test_callback", my_callback)

        assert CallbackRegistry.has("test_callback")
        retrieved = CallbackRegistry.get("test_callback")
        assert retrieved is my_callback
        assert retrieved() == "test"

    def test_encode_decode(self):
        """Test encoding and decoding callbacks."""

        def heal_player(entity, context):
            entity.heal(50)

        CallbackRegistry.register("heal_player", heal_player)

        # Encode
        key = CallbackRegistry.encode(heal_player)
        assert key == "heal_player"

        # Decode
        restored = CallbackRegistry.decode(key)
        assert restored is heal_player

    def test_encode_none(self):
        """Test encoding None callback."""
        key = CallbackRegistry.encode(None)
        assert key is None

    def test_decode_none(self):
        """Test decoding None key."""
        callback = CallbackRegistry.decode(None)
        assert callback is None

    def test_auto_register_warning(self):
        """Test auto-registration with warning."""

        def unregistered_callback():
            pass

        # Should auto-register with warning
        with pytest.warns(UserWarning):
            key = CallbackRegistry.encode(unregistered_callback)

        assert key is not None
        assert CallbackRegistry.has(key)


class TestSaveManager:
    """Test save manager functionality."""

    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SaveManager(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load(self):
        """Test basic save and load."""
        save_data = {"player": {"name": "Hero", "level": 5}, "location": "Village"}

        # Save
        success = self.manager.save("test_save", save_data)
        assert success

        # Load
        loaded = self.manager.load("test_save")
        assert loaded is not None
        assert loaded["player"]["name"] == "Hero"
        assert loaded["player"]["level"] == 5
        assert loaded["location"] == "Village"

    def test_list_saves(self):
        """Test listing save files."""
        self.manager.save("save1", {"data": 1})
        self.manager.save("save2", {"data": 2})

        saves = self.manager.list_saves()
        assert "save1" in saves
        assert "save2" in saves

    def test_delete_save(self):
        """Test deleting save files."""
        self.manager.save("to_delete", {"data": 1})
        assert self.manager.exists("to_delete")

        success = self.manager.delete("to_delete")
        assert success
        assert not self.manager.exists("to_delete")

    def test_get_save_info(self):
        """Test getting save metadata."""
        self.manager.save("info_test", {"data": 1})

        info = self.manager.get_save_info("info_test")
        assert info is not None
        assert "version" in info
        assert "timestamp" in info
        assert info["save_name"] == "info_test"


class TestItemSerialization:
    """Test item serialization."""

    def setup_method(self):
        """Clear callback registry."""
        CallbackRegistry.clear()

    def test_simple_item_roundtrip(self):
        """Test serializing and deserializing a simple item."""
        sword = create_weapon("Iron Sword", base_damage=10, value=50)

        # Serialize
        data = sword.to_dict()
        assert data["name"] == "Iron Sword"
        assert data["base_damage"] == 10
        assert data["value"] == 50

        # Deserialize
        restored = Item.from_dict(data)
        assert restored.name == "Iron Sword"
        assert restored.base_damage == 10
        assert restored.value == 50
        assert restored.item_type == ItemType.WEAPON

    def test_consumable_with_callback(self):
        """Test serializing consumable with callback."""

        def heal_50(entity, context):
            entity.heal(50)

        CallbackRegistry.register("heal_50", heal_50)

        potion = create_consumable("Health Potion", on_use=heal_50)

        # Serialize
        data = potion.to_dict()
        assert "on_use_callback" in data
        assert data["on_use_callback"] == "heal_50"

        # Deserialize
        restored = Item.from_dict(data)
        assert restored.on_use is heal_50


class TestInventorySerialization:
    """Test inventory serialization."""

    def test_inventory_roundtrip(self):
        """Test serializing and deserializing inventory."""
        inv = Inventory(max_slots=20, gold=100)
        inv.add_item(create_weapon("Sword", base_damage=10))
        inv.add_item(create_weapon("Bow", base_damage=8, range=5))

        # Serialize
        data = inv.to_dict()
        assert data["gold"] == 100
        assert data["max_slots"] == 20
        assert len(data["items"]) == 2

        # Deserialize
        restored = Inventory.from_dict(data)
        assert restored.gold == 100
        assert restored.max_slots == 20
        assert len(restored.items) == 2
        assert restored.items[0].name == "Sword"
        assert restored.items[1].name == "Bow"


class TestEntitySerialization:
    """Test entity serialization."""

    def test_character_roundtrip(self):
        """Test serializing and deserializing a character."""
        hero = Character(
            name="Hero", stats=Stats(hp=100, max_hp=100, atk=15, defense=10, level=5)
        )
        hero.init_inventory()
        hero.inventory.add_gold(500)
        hero.inventory.add_item(create_weapon("Sword", base_damage=10))

        # Serialize
        data = hero.to_dict()
        assert data["name"] == "Hero"
        assert data["stats"]["hp"] == 100
        assert data["stats"]["level"] == 5
        assert "inventory" in data

        # Deserialize
        restored = Character.from_dict(data)
        assert restored.name == "Hero"
        assert restored.stats.hp == 100
        assert restored.stats.level == 5
        assert restored.inventory is not None
        assert restored.inventory.gold == 500
        assert len(restored.inventory.items) == 1


class TestPartySerialization:
    """Test party serialization."""

    def test_party_roundtrip(self):
        """Test serializing and deserializing a party."""
        hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
        mage = Character(name="Mage", stats=Stats(hp=80, atk=10))

        party = Party(name="Adventurers")
        party.add_member(hero)
        party.add_member(mage)
        party.metadata["gold"] = 1000

        # Serialize
        data = party.to_dict()
        assert data["name"] == "Adventurers"
        assert len(data["member_ids"]) == 2
        assert data["metadata"]["gold"] == 1000

        # Create entity lookup
        entity_lookup = {hero.id: hero, mage.id: mage}

        # Deserialize
        restored = Party.from_dict(data, entity_lookup)
        assert restored.name == "Adventurers"
        assert len(restored.members) == 2
        assert restored.members[0].name == "Hero"
        assert restored.members[1].name == "Mage"
        assert restored.metadata["gold"] == 1000


class TestQuestSerialization:
    """Test quest serialization."""

    def setup_method(self):
        """Clear callback registry."""
        CallbackRegistry.clear()

    def test_quest_objective_roundtrip(self):
        """Test serializing and deserializing quest objectives."""
        objective = QuestObjective(
            description="Defeat 5 goblins",
            objective_type=ObjectiveType.KILL_ENEMY,
            target="Goblin",
            target_count=5,
            current_count=2,
        )

        # Serialize
        data = objective.to_dict()
        assert data["description"] == "Defeat 5 goblins"
        assert data["target"] == "Goblin"
        assert data["target_count"] == 5
        assert data["current_count"] == 2

        # Deserialize
        restored = QuestObjective.from_dict(data)
        assert restored.description == "Defeat 5 goblins"
        assert restored.objective_type == ObjectiveType.KILL_ENEMY
        assert restored.target == "Goblin"
        assert restored.target_count == 5
        assert restored.current_count == 2

    def test_quest_roundtrip(self):
        """Test serializing and deserializing quests."""
        quest = Quest(
            name="Save the Village",
            description="Defeat the goblin chief",
            exp_reward=100,
            gold_reward=50,
            status=QuestStatus.ACTIVE,
        )
        quest.add_objective(
            QuestObjective(
                description="Defeat goblin chief",
                objective_type=ObjectiveType.KILL_ENEMY,
                target="Goblin Chief",
            )
        )

        # Serialize
        data = quest.to_dict()
        assert data["name"] == "Save the Village"
        assert data["exp_reward"] == 100
        assert data["status"] == "ACTIVE"
        assert len(data["objectives"]) == 1

        # Deserialize (without auto-register to avoid duplicate)
        restored = Quest.from_dict(data, auto_register=False)
        assert restored.name == "Save the Village"
        assert restored.status == QuestStatus.ACTIVE
        assert restored.exp_reward == 100
        assert len(restored.objectives) == 1
        assert restored.objectives[0].description == "Defeat goblin chief"


class TestGameSaveLoad:
    """Test full game save/load functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        CallbackRegistry.clear()

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_game_save_to_file(self):
        """Test saving game to file."""
        config = GameConfig(save_directory=self.temp_dir)
        game = Game(config)

        # Add some entities
        hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
        game.register_entity(hero)

        # Add some items
        sword = create_weapon("Sword", base_damage=10)
        game.register_item(sword)

        # Save
        success = game.save_to_file("test_game")
        assert success

        # Check file exists
        assert game.save_manager.exists("test_game")

    def test_game_load_from_file(self):
        """Test loading game from file."""
        config = GameConfig(save_directory=self.temp_dir)
        game = Game(config)

        # Create and register entities
        hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
        hero.init_inventory()
        hero.inventory.add_gold(500)
        game.register_entity(hero)

        # Save
        game.save_to_file("load_test")

        # Create new game and load
        game2 = Game(config)
        success = game2.load_from_file("load_test")
        assert success

        # Verify loaded data
        loaded_hero = game2.get_entity(hero.id)
        assert loaded_hero is not None
        assert loaded_hero.name == "Hero"
        assert loaded_hero.stats.hp == 100
        assert loaded_hero.inventory.gold == 500

    def test_game_list_and_delete_saves(self):
        """Test listing and deleting saves."""
        config = GameConfig(save_directory=self.temp_dir)
        game = Game(config)

        # Create multiple saves
        game.save_to_file("save1")
        game.save_to_file("save2")
        game.save_to_file("save3")

        # List saves
        saves = game.list_saves()
        assert "save1" in saves
        assert "save2" in saves
        assert "save3" in saves

        # Delete one
        success = game.delete_save("save2")
        assert success

        # Verify deletion
        saves = game.list_saves()
        assert "save1" in saves
        assert "save2" not in saves
        assert "save3" in saves

    def test_game_state_persistence(self):
        """Test that game state persists across save/load."""
        config = GameConfig(save_directory=self.temp_dir)
        game = Game(config)

        # Set game state
        game.clock_time = 123.45
        game.data["custom_flag"] = True
        game.data["player_name"] = "TestPlayer"

        # Save and load
        game.save_to_file("state_test")
        game2 = Game(config)
        game2.load_from_file("state_test")

        # Verify state
        assert game2.clock_time == 123.45
        assert game2.data["custom_flag"] is True
        assert game2.data["player_name"] == "TestPlayer"
