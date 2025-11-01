"""Data loaders for JSON and YAML files.

This module provides utilities for loading game data from files,
supporting the hybrid code/data approach.
"""

import json
import yaml  # type: ignore[import-untyped]
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..entities import Stats, Character, NPC, Enemy
from ..items import (
    Item,
    ItemType,
    EquipSlot,
    create_weapon,
    create_armor,
    create_consumable,
)
from ..dialog import DialogNode, DialogChoice, DialogTree
from ..quests import Quest, QuestObjective, ObjectiveType


class DataLoader:
    """Base data loader for game content.

    Example:
        >>> loader = DataLoader()
        >>> items = loader.load_items("data/items.json")
        >>> npcs = loader.load_npcs("data/npcs.yaml")
    """

    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Load JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """Load YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data
        """
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_file(file_path: str) -> Dict[str, Any]:
        """Load file (auto-detect JSON or YAML).

        Args:
            file_path: Path to file

        Returns:
            Parsed data
        """
        path = Path(file_path)
        if path.suffix.lower() in [".yaml", ".yml"]:
            return DataLoader.load_yaml(file_path)
        elif path.suffix.lower() == ".json":
            return DataLoader.load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
        """Save data to JSON file.

        Args:
            data: Data to save
            file_path: Output file path
            indent: JSON indentation
        """
        with open(file_path, "w") as f:
            json.dump(data, f, indent=indent)

    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str) -> None:
        """Save data to YAML file.

        Args:
            data: Data to save
            file_path: Output file path
        """
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


class ItemLoader:
    """Loader for items from data files."""

    @staticmethod
    def load_items(file_path: str) -> List[Item]:
        """Load items from a data file.

        Args:
            file_path: Path to items file

        Returns:
            List of items

        File format example (JSON):
        {
            "items": [
                {
                    "name": "Iron Sword",
                    "type": "weapon",
                    "description": "A basic iron sword",
                    "atk": 10,
                    "value": 50
                }
            ]
        }
        """
        data = DataLoader.load_file(file_path)
        items = []

        for item_data in data.get("items", []):
            item_type = item_data.get("type", "misc").lower()

            if item_type == "weapon":
                item = create_weapon(
                    name=item_data["name"],
                    base_damage=item_data.get("atk", 0),
                    description=item_data.get("description", ""),
                    value=item_data.get("value", 0),
                )
            elif item_type == "armor":
                slot_name = item_data.get("slot", "body")
                slot = EquipSlot[slot_name.upper()]
                item = create_armor(
                    name=item_data["name"],
                    defense=item_data.get("defense", 0),
                    slot=slot,
                    description=item_data.get("description", ""),
                    value=item_data.get("value", 0),
                )
            elif item_type == "consumable":
                # For consumables, we can't load the on_use function from data
                # So we create a basic item and let the user set the function
                item = Item(
                    name=item_data["name"],
                    description=item_data.get("description", ""),
                    item_type=ItemType.CONSUMABLE,
                    consumable=True,
                    value=item_data.get("value", 0),
                    stackable=item_data.get("stackable", True),
                    max_stack=item_data.get("max_stack", 99),
                )
            else:
                # Generic item
                item = Item(
                    name=item_data["name"],
                    description=item_data.get("description", ""),
                    item_type=(
                        ItemType[item_type.upper()]
                        if hasattr(ItemType, item_type.upper())
                        else ItemType.MISC
                    ),
                    value=item_data.get("value", 0),
                )

            items.append(item)

        return items


class EntityLoader:
    """Loader for entities (NPCs, enemies) from data files."""

    @staticmethod
    def load_npcs(file_path: str) -> List[NPC]:
        """Load NPCs from a data file.

        Args:
            file_path: Path to NPCs file

        Returns:
            List of NPCs

        File format example (YAML):
        npcs:
          - name: Village Elder
            description: An old wise man
            stats:
              hp: 100
              atk: 5
            dialog_tree_id: elder_dialog
        """
        data = DataLoader.load_file(file_path)
        npcs = []

        for npc_data in data.get("npcs", []):
            stats_data = npc_data.get("stats", {})
            stats = Stats(**stats_data)

            npc = NPC(
                name=npc_data["name"],
                description=npc_data.get("description", ""),
                stats=stats,
                dialog_tree_id=npc_data.get("dialog_tree_id"),
                quest_ids=npc_data.get("quest_ids", []),
                is_merchant=npc_data.get("is_merchant", False),
            )

            npcs.append(npc)

        return npcs

    @staticmethod
    def load_enemies(file_path: str) -> List[Enemy]:
        """Load enemies from a data file.

        Args:
            file_path: Path to enemies file

        Returns:
            List of enemies
        """
        data = DataLoader.load_file(file_path)
        enemies = []

        for enemy_data in data.get("enemies", []):
            stats_data = enemy_data.get("stats", {})
            stats = Stats(**stats_data)

            enemy = Enemy(
                name=enemy_data["name"],
                description=enemy_data.get("description", ""),
                stats=stats,
                ai_type=enemy_data.get("ai_type", "aggressive"),
                exp_reward=enemy_data.get("exp_reward", 10),
                gold_reward=enemy_data.get("gold_reward", 5),
                loot_table=enemy_data.get("loot_table", []),
            )

            enemies.append(enemy)

        return enemies


class DialogLoader:
    """Loader for dialog trees from data files."""

    @staticmethod
    def load_dialog_tree(file_path: str) -> DialogTree:
        """Load a dialog tree from a data file.

        Args:
            file_path: Path to dialog file

        Returns:
            Dialog tree

        File format example (YAML):
        name: Village Elder Dialog
        start_node: greeting
        nodes:
          - id: greeting
            speaker: Village Elder
            text: "Welcome, traveler!"
            choices:
              - text: "Tell me about the village"
                next_node: village_info
              - text: "Goodbye"
                next_node: null
          - id: village_info
            speaker: Village Elder
            text: "Our village has been here for centuries..."
            choices:
              - text: "I see"
                next_node: null
        """
        data = DataLoader.load_file(file_path)

        tree = DialogTree(name=data["name"], start_node_id=data.get("start_node"))

        for node_data in data.get("nodes", []):
            choices = []
            for choice_data in node_data.get("choices", []):
                choice = DialogChoice(
                    text=choice_data["text"], next_node_id=choice_data.get("next_node")
                )
                choices.append(choice)

            node = DialogNode(
                id=node_data["id"],
                speaker=node_data.get("speaker"),
                text=node_data["text"],
                choices=choices,
            )

            tree.add_node(node)

        return tree


class QuestLoader:
    """Loader for quests from data files."""

    @staticmethod
    def load_quests(file_path: str) -> List[Quest]:
        """Load quests from a data file.

        Args:
            file_path: Path to quests file

        Returns:
            List of quests

        File format example (JSON):
        {
            "quests": [
                {
                    "name": "Save the Village",
                    "description": "Help defend the village",
                    "objectives": [
                        {
                            "description": "Defeat 5 goblins",
                            "type": "kill_enemy",
                            "target": "Goblin",
                            "count": 5
                        }
                    ],
                    "exp_reward": 100,
                    "gold_reward": 50
                }
            ]
        }
        """
        data = DataLoader.load_file(file_path)
        quests = []

        for quest_data in data.get("quests", []):
            quest = Quest(
                name=quest_data["name"],
                description=quest_data.get("description", ""),
                exp_reward=quest_data.get("exp_reward", 0),
                gold_reward=quest_data.get("gold_reward", 0),
                item_rewards=quest_data.get("item_rewards", []),
                required_level=quest_data.get("required_level", 1),
            )

            for obj_data in quest_data.get("objectives", []):
                obj_type_str = obj_data.get("type", "custom").upper()
                obj_type = (
                    ObjectiveType[obj_type_str]
                    if hasattr(ObjectiveType, obj_type_str)
                    else ObjectiveType.CUSTOM
                )

                objective = QuestObjective(
                    description=obj_data["description"],
                    objective_type=obj_type,
                    target=obj_data.get("target"),
                    target_count=obj_data.get("count", 1),
                )

                quest.add_objective(objective)

            quests.append(quest)

        return quests
