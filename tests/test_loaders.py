"""Tests for data loaders (JSON/YAML loading)."""

import json
import os
import shutil
import tempfile

import pytest
import yaml  # type: ignore[import-untyped]

from barebones_rpg.loaders import (
    DataLoader,
    ItemLoader,
    EntityLoader,
    DialogLoader,
    QuestLoader,
)
from barebones_rpg.items.item import ItemType, EquipSlot
from barebones_rpg.quests.quest import ObjectiveType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


class TestDataLoader:
    """Tests for DataLoader base class."""

    def test_file_format_detection(self, temp_dir):
        """Test that load_file auto-detects JSON, YAML, and YML formats."""
        data = {"test": "value", "number": 42}

        # Test JSON
        json_path = os.path.join(temp_dir, "test.json")
        DataLoader.save_json(data, json_path)
        loaded = DataLoader.load_file(json_path)
        assert loaded == data

        # Test YAML
        yaml_path = os.path.join(temp_dir, "test.yaml")
        DataLoader.save_yaml(data, yaml_path)
        loaded = DataLoader.load_file(yaml_path)
        assert loaded == data

        # Test YML extension
        yml_path = os.path.join(temp_dir, "test.yml")
        DataLoader.save_yaml(data, yml_path)
        loaded = DataLoader.load_file(yml_path)
        assert loaded == data

        # Test unsupported extension raises ValueError
        with pytest.raises(ValueError, match="Unsupported file format"):
            DataLoader.load_file(os.path.join(temp_dir, "test.txt"))

    def test_file_errors(self, temp_dir):
        """Test error handling for file operations."""
        # Non-existent file
        with pytest.raises(FileNotFoundError):
            DataLoader.load_json(os.path.join(temp_dir, "nonexistent.json"))

        # Invalid JSON
        invalid_json_path = os.path.join(temp_dir, "invalid.json")
        with open(invalid_json_path, "w") as f:
            f.write("{invalid json content")
        with pytest.raises(json.JSONDecodeError):
            DataLoader.load_json(invalid_json_path)

        # Invalid YAML
        invalid_yaml_path = os.path.join(temp_dir, "invalid.yaml")
        with open(invalid_yaml_path, "w") as f:
            f.write("key: [unclosed bracket")
        with pytest.raises(yaml.YAMLError):
            DataLoader.load_yaml(invalid_yaml_path)

    def test_save_and_load_roundtrip(self, temp_dir):
        """Test save/load roundtrip for JSON and YAML."""
        data = {
            "string": "hello",
            "number": 123,
            "float": 3.14,
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
        }

        # JSON roundtrip
        json_path = os.path.join(temp_dir, "roundtrip.json")
        DataLoader.save_json(data, json_path)
        loaded = DataLoader.load_json(json_path)
        assert loaded == data

        # YAML roundtrip
        yaml_path = os.path.join(temp_dir, "roundtrip.yaml")
        DataLoader.save_yaml(data, yaml_path)
        loaded = DataLoader.load_yaml(yaml_path)
        assert loaded == data


class TestItemLoader:
    """Tests for ItemLoader."""

    def test_load_all_item_types(self, temp_dir):
        """Test loading weapons, armor, consumables, and misc items."""
        items_data = {
            "items": [
                {
                    "name": "Iron Sword",
                    "type": "weapon",
                    "description": "A basic sword",
                    "atk": 10,
                    "value": 50,
                },
                {
                    "name": "Steel Helmet",
                    "type": "armor",
                    "slot": "head",
                    "defense": 5,
                    "description": "Protective headgear",
                    "value": 75,
                },
                {
                    "name": "Health Potion",
                    "type": "consumable",
                    "stackable": True,
                    "max_stack": 20,
                    "value": 25,
                },
                {
                    "name": "Old Key",
                    "type": "key",
                    "description": "Opens something",
                },
                {
                    "name": "Strange Rock",
                    "type": "unknown_type",
                },
            ]
        }

        path = os.path.join(temp_dir, "items.json")
        DataLoader.save_json(items_data, path)
        items = ItemLoader.load_items(path)

        assert len(items) == 5

        # Weapon
        sword = items[0]
        assert sword.name == "Iron Sword"
        assert sword.item_type == ItemType.WEAPON
        assert sword.base_damage == 10
        assert sword.description == "A basic sword"
        assert sword.value == 50
        assert sword.equip_slot == EquipSlot.WEAPON

        # Armor
        helmet = items[1]
        assert helmet.name == "Steel Helmet"
        assert helmet.item_type == ItemType.ARMOR
        assert helmet.equip_slot == EquipSlot.HEAD
        assert helmet.description == "Protective headgear"
        assert helmet.value == 75

        # Consumable
        potion = items[2]
        assert potion.name == "Health Potion"
        assert potion.item_type == ItemType.CONSUMABLE
        assert potion.consumable is True
        assert potion.stackable is True
        assert potion.max_stack == 20

        # Key item (valid ItemType)
        key = items[3]
        assert key.name == "Old Key"
        assert key.item_type == ItemType.KEY
        assert key.description == "Opens something"

        # Unknown type falls back to MISC
        rock = items[4]
        assert rock.name == "Strange Rock"
        assert rock.item_type == ItemType.MISC

    def test_item_loader_edge_cases(self, temp_dir):
        """Test edge cases: empty list, missing keys, invalid slot."""
        # Empty items list
        path1 = os.path.join(temp_dir, "empty.json")
        DataLoader.save_json({"items": []}, path1)
        assert ItemLoader.load_items(path1) == []

        # Missing "items" key returns empty list
        path2 = os.path.join(temp_dir, "no_items_key.json")
        DataLoader.save_json({"other": "data"}, path2)
        assert ItemLoader.load_items(path2) == []

        # Missing required "name" field raises KeyError
        path3 = os.path.join(temp_dir, "no_name.json")
        DataLoader.save_json({"items": [{"type": "weapon"}]}, path3)
        with pytest.raises(KeyError):
            ItemLoader.load_items(path3)

        # Invalid armor slot raises KeyError
        path4 = os.path.join(temp_dir, "bad_slot.json")
        DataLoader.save_json(
            {"items": [{"name": "Bad Armor", "type": "armor", "slot": "invalid_slot"}]},
            path4,
        )
        with pytest.raises(KeyError):
            ItemLoader.load_items(path4)

    def test_item_loader_defaults(self, temp_dir):
        """Test that default values are applied correctly."""
        items_data = {
            "items": [
                {"name": "Minimal Item"},
                {"name": "Minimal Weapon", "type": "weapon"},
            ]
        }

        path = os.path.join(temp_dir, "minimal.json")
        DataLoader.save_json(items_data, path)
        items = ItemLoader.load_items(path)

        # Generic item with defaults
        generic = items[0]
        assert generic.description == ""
        assert generic.value == 0
        assert generic.item_type == ItemType.MISC

        # Weapon with defaults
        weapon = items[1]
        assert weapon.base_damage == 0
        assert weapon.description == ""
        assert weapon.value == 0


class TestEntityLoader:
    """Tests for EntityLoader (NPCs and Enemies)."""

    def test_load_npcs_and_enemies(self, temp_dir):
        """Test loading NPCs and enemies with various configurations."""
        # NPC data
        npc_data = {
            "npcs": [
                {
                    "name": "Village Elder",
                    "description": "An old wise man",
                    "stats": {"hp": 100, "strength": 8},
                    "dialog_tree_id": "elder_dialog",
                    "quest_ids": ["quest1", "quest2"],
                    "is_merchant": True,
                },
                {"name": "Villager"},
            ]
        }

        npc_path = os.path.join(temp_dir, "npcs.yaml")
        DataLoader.save_yaml(npc_data, npc_path)
        npcs = EntityLoader.load_npcs(npc_path)

        assert len(npcs) == 2

        # Full NPC
        elder = npcs[0]
        assert elder.name == "Village Elder"
        assert elder.description == "An old wise man"
        assert elder.stats.hp == 100
        assert elder.stats.strength == 8
        assert elder.dialog_tree_id == "elder_dialog"
        assert elder.quest_ids == ["quest1", "quest2"]
        assert elder.is_merchant is True

        # Minimal NPC with defaults
        villager = npcs[1]
        assert villager.name == "Villager"
        assert villager.description == ""
        assert villager.quest_ids == []
        assert villager.is_merchant is False

        # Enemy data
        enemy_data = {
            "enemies": [
                {
                    "name": "Goblin",
                    "description": "A small green creature",
                    "stats": {"hp": 30, "strength": 8},
                    "ai_type": "aggressive",
                    "exp_reward": 25,
                    "gold_reward": 10,
                    "loot_table": [{"item": "Gold Coin", "chance": 0.8}],
                },
                {"name": "Skeleton"},
            ]
        }

        enemy_path = os.path.join(temp_dir, "enemies.yaml")
        DataLoader.save_yaml(enemy_data, enemy_path)
        enemies = EntityLoader.load_enemies(enemy_path)

        assert len(enemies) == 2

        # Full enemy
        goblin = enemies[0]
        assert goblin.name == "Goblin"
        assert goblin.description == "A small green creature"
        assert goblin.stats.hp == 30
        assert goblin.ai_type == "aggressive"
        assert goblin.exp_reward == 25
        assert goblin.gold_reward == 10
        assert len(goblin.loot_table) == 1

        # Minimal enemy with defaults
        skeleton = enemies[1]
        assert skeleton.name == "Skeleton"
        assert skeleton.exp_reward == 10  # default
        assert skeleton.gold_reward == 5  # default
        assert skeleton.loot_table == []

    def test_entity_loader_empty_data(self, temp_dir):
        """Test that empty/missing keys return empty lists."""
        # Empty npcs list
        path1 = os.path.join(temp_dir, "empty_npcs.json")
        DataLoader.save_json({"npcs": []}, path1)
        assert EntityLoader.load_npcs(path1) == []

        # Missing npcs key
        path2 = os.path.join(temp_dir, "no_npcs.json")
        DataLoader.save_json({}, path2)
        assert EntityLoader.load_npcs(path2) == []

        # Same for enemies
        path3 = os.path.join(temp_dir, "no_enemies.json")
        DataLoader.save_json({}, path3)
        assert EntityLoader.load_enemies(path3) == []


class TestDialogLoader:
    """Tests for DialogLoader."""

    def test_load_dialog_tree(self, temp_dir):
        """Test loading a dialog tree with nodes and choices."""
        dialog_data = {
            "name": "Merchant Dialog",
            "start_node": "greeting",
            "nodes": [
                {
                    "id": "greeting",
                    "speaker": "Merchant",
                    "text": "Welcome to my shop!",
                    "choices": [
                        {"text": "Show me your wares", "next_node": "shop"},
                        {"text": "Goodbye", "next_node": None},
                    ],
                },
                {
                    "id": "shop",
                    "speaker": "Merchant",
                    "text": "Here's what I have for sale.",
                    "choices": [{"text": "Thanks", "next_node": None}],
                },
            ],
        }

        path = os.path.join(temp_dir, "dialog.yaml")
        DataLoader.save_yaml(dialog_data, path)
        tree = DialogLoader.load_dialog_tree(path)

        assert tree.name == "Merchant Dialog"
        assert tree.start_node_id == "greeting"

        # Check nodes
        greeting = tree.get_node("greeting")
        assert greeting is not None
        assert greeting.speaker == "Merchant"
        assert greeting.text == "Welcome to my shop!"
        assert len(greeting.choices) == 2
        assert greeting.choices[0].text == "Show me your wares"
        assert greeting.choices[0].next_node_id == "shop"
        assert greeting.choices[1].next_node_id is None

        shop = tree.get_node("shop")
        assert shop is not None
        assert shop.text == "Here's what I have for sale."

    def test_dialog_loader_edge_cases(self, temp_dir):
        """Test dialog loader edge cases."""
        # Empty nodes list
        path1 = os.path.join(temp_dir, "empty_dialog.yaml")
        DataLoader.save_yaml({"name": "Empty Dialog", "nodes": []}, path1)
        tree = DialogLoader.load_dialog_tree(path1)
        assert tree.name == "Empty Dialog"

        # Missing name raises KeyError
        path2 = os.path.join(temp_dir, "no_name_dialog.yaml")
        DataLoader.save_yaml({"nodes": []}, path2)
        with pytest.raises(KeyError):
            DialogLoader.load_dialog_tree(path2)

        # Node missing text raises KeyError
        path3 = os.path.join(temp_dir, "bad_node.yaml")
        DataLoader.save_yaml(
            {"name": "Bad Dialog", "nodes": [{"id": "test"}]},
            path3,
        )
        with pytest.raises(KeyError):
            DialogLoader.load_dialog_tree(path3)


class TestQuestLoader:
    """Tests for QuestLoader."""

    def test_load_quests(self, temp_dir):
        """Test loading quests with various objective types."""
        quest_data = {
            "quests": [
                {
                    "name": "Goblin Slayer",
                    "description": "Defeat the goblins terrorizing the village",
                    "exp_reward": 100,
                    "gold_reward": 50,
                    "required_level": 2,
                    "objectives": [
                        {
                            "description": "Kill 5 goblins",
                            "type": "kill_enemy",
                            "target": "Goblin",
                            "count": 5,
                        },
                        {
                            "description": "Collect goblin ears",
                            "type": "COLLECT_ITEM",
                            "target": "Goblin Ear",
                            "count": 3,
                        },
                    ],
                },
                {
                    "name": "Simple Quest",
                    "objectives": [
                        {
                            "description": "Do something",
                            "type": "invalid_type",
                        }
                    ],
                },
            ]
        }

        path = os.path.join(temp_dir, "quests.json")
        DataLoader.save_json(quest_data, path)
        quests = QuestLoader.load_quests(path)

        assert len(quests) == 2

        # Full quest
        goblin_quest = quests[0]
        assert goblin_quest.name == "Goblin Slayer"
        assert goblin_quest.description == "Defeat the goblins terrorizing the village"
        assert goblin_quest.exp_reward == 100
        assert goblin_quest.gold_reward == 50
        assert goblin_quest.required_level == 2
        assert len(goblin_quest.objectives) == 2

        # Check objectives
        obj1 = goblin_quest.objectives[0]
        assert obj1.description == "Kill 5 goblins"
        assert obj1.objective_type == ObjectiveType.KILL_ENEMY
        assert obj1.target == "Goblin"
        assert obj1.target_count == 5

        obj2 = goblin_quest.objectives[1]
        assert obj2.objective_type == ObjectiveType.COLLECT_ITEM
        assert obj2.target_count == 3

        # Quest with invalid objective type falls back to CUSTOM
        simple_quest = quests[1]
        assert simple_quest.objectives[0].objective_type == ObjectiveType.CUSTOM

    def test_quest_loader_defaults(self, temp_dir):
        """Test quest loader applies correct defaults."""
        quest_data = {
            "quests": [
                {
                    "name": "Minimal Quest",
                }
            ]
        }

        path = os.path.join(temp_dir, "minimal_quest.json")
        DataLoader.save_json(quest_data, path)
        quests = QuestLoader.load_quests(path)

        quest = quests[0]
        assert quest.description == ""
        assert quest.exp_reward == 0
        assert quest.gold_reward == 0
        assert quest.required_level == 1
        assert quest.item_rewards == []
        assert quest.objectives == []

    def test_quest_loader_edge_cases(self, temp_dir):
        """Test quest loader edge cases."""
        # Empty quests list
        path1 = os.path.join(temp_dir, "empty_quests.json")
        DataLoader.save_json({"quests": []}, path1)
        assert QuestLoader.load_quests(path1) == []

        # Missing quests key
        path2 = os.path.join(temp_dir, "no_quests.json")
        DataLoader.save_json({}, path2)
        assert QuestLoader.load_quests(path2) == []

        # Missing quest name raises KeyError
        path3 = os.path.join(temp_dir, "no_name_quest.json")
        DataLoader.save_json({"quests": [{"description": "No name"}]}, path3)
        with pytest.raises(KeyError):
            QuestLoader.load_quests(path3)

        # Missing objective description raises KeyError
        path4 = os.path.join(temp_dir, "bad_objective.json")
        DataLoader.save_json(
            {"quests": [{"name": "Quest", "objectives": [{"type": "custom"}]}]},
            path4,
        )
        with pytest.raises(KeyError):
            QuestLoader.load_quests(path4)
