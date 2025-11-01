"""Tests for the party system."""

import pytest
from barebones_rpg.party import Party
from barebones_rpg.entities import Character, Enemy, Stats
from barebones_rpg.combat import Combat
from barebones_rpg.core import EventManager


@pytest.fixture
def hero():
    """Create a test hero."""
    return Character(name="Hero", stats=Stats(hp=100, atk=15, speed=10))


@pytest.fixture
def mage():
    """Create a test mage."""
    return Character(name="Mage", stats=Stats(hp=80, atk=10, speed=8))


@pytest.fixture
def warrior():
    """Create a test warrior."""
    return Character(name="Warrior", stats=Stats(hp=120, atk=18, speed=6))


@pytest.fixture
def goblin():
    """Create a test goblin."""
    return Enemy(name="Goblin", stats=Stats(hp=30, atk=5, speed=7))


@pytest.fixture
def orc():
    """Create a test orc."""
    return Enemy(name="Orc", stats=Stats(hp=50, atk=10, speed=5))


class TestPartyBasics:
    """Test basic party functionality."""

    def test_create_empty_party(self):
        """Test creating an empty party."""
        party = Party(name="Adventurers")
        assert party.name == "Adventurers"
        assert party.size() == 0
        assert party.members == []

    def test_create_party_with_members(self, hero, mage):
        """Test creating a party with initial members."""
        party = Party(name="Heroes", members=[hero, mage])
        assert party.size() == 2
        assert hero in party.members
        assert mage in party.members

    def test_add_member(self, hero):
        """Test adding a member to a party."""
        party = Party(name="Adventurers")
        assert party.add_member(hero) is True
        assert party.size() == 1
        assert party.has_member(hero)

    def test_add_duplicate_member(self, hero):
        """Test that adding a duplicate member returns False."""
        party = Party(name="Adventurers")
        party.add_member(hero)
        assert party.add_member(hero) is False
        assert party.size() == 1

    def test_remove_member(self, hero, mage):
        """Test removing a member from a party."""
        party = Party(name="Adventurers", members=[hero, mage])
        assert party.remove_member(hero) is True
        assert party.size() == 1
        assert not party.has_member(hero)
        assert party.has_member(mage)

    def test_remove_nonexistent_member(self, hero, mage):
        """Test that removing a non-existent member returns False."""
        party = Party(name="Adventurers", members=[hero])
        assert party.remove_member(mage) is False
        assert party.size() == 1

    def test_clear_party(self, hero, mage):
        """Test clearing all members from a party."""
        party = Party(name="Adventurers", members=[hero, mage])
        party.clear()
        assert party.size() == 0
        assert party.members == []

    def test_has_member(self, hero, mage):
        """Test checking if a party has a specific member."""
        party = Party(name="Adventurers", members=[hero])
        assert party.has_member(hero) is True
        assert party.has_member(mage) is False


class TestPartyStatus:
    """Test party status checks."""

    def test_get_alive_members(self, hero, mage):
        """Test getting alive members."""
        party = Party(name="Adventurers", members=[hero, mage])
        alive = party.get_alive_members()
        assert len(alive) == 2
        assert hero in alive
        assert mage in alive

    def test_get_alive_members_with_dead(self, hero, mage):
        """Test getting alive members when some are dead."""
        party = Party(name="Adventurers", members=[hero, mage])
        hero.stats.hp = 0
        alive = party.get_alive_members()
        assert len(alive) == 1
        assert mage in alive
        assert hero not in alive

    def test_is_not_defeated(self, hero, mage):
        """Test that party is not defeated when members are alive."""
        party = Party(name="Adventurers", members=[hero, mage])
        assert party.is_defeated() is False

    def test_is_defeated_when_all_dead(self, hero, mage):
        """Test that party is defeated when all members are dead."""
        party = Party(name="Adventurers", members=[hero, mage])
        hero.stats.hp = 0
        mage.stats.hp = 0
        assert party.is_defeated() is True

    def test_is_defeated_empty_party(self):
        """Test that empty party is considered defeated."""
        party = Party(name="Adventurers")
        assert party.is_defeated() is True


class TestPartyLeader:
    """Test party leader functionality."""

    def test_get_leader_single_member(self, hero):
        """Test getting leader with single member."""
        party = Party(name="Adventurers", members=[hero])
        assert party.get_leader() == hero

    def test_get_leader_multiple_members(self, hero, mage):
        """Test that leader is first member."""
        party = Party(name="Adventurers", members=[hero, mage])
        assert party.get_leader() == hero

    def test_get_leader_empty_party(self):
        """Test getting leader from empty party."""
        party = Party(name="Adventurers")
        assert party.get_leader() is None

    def test_leader_changes_on_removal(self, hero, mage):
        """Test that leader changes when first member is removed."""
        party = Party(name="Adventurers", members=[hero, mage])
        assert party.get_leader() == hero
        party.remove_member(hero)
        assert party.get_leader() == mage


class TestPartyMetadata:
    """Test party metadata extensibility."""

    def test_metadata_initially_empty(self):
        """Test that metadata dict is initially empty."""
        party = Party(name="Adventurers")
        assert party.metadata == {}

    def test_metadata_custom_values(self):
        """Test storing custom values in metadata."""
        party = Party(name="Adventurers")
        party.metadata["gold"] = 100
        party.metadata["formation"] = "defensive"
        party.metadata["level"] = 5
        assert party.metadata["gold"] == 100
        assert party.metadata["formation"] == "defensive"
        assert party.metadata["level"] == 5

    def test_metadata_in_constructor(self):
        """Test setting metadata in constructor."""
        party = Party(name="Adventurers", metadata={"gold": 50, "reputation": "good"})
        assert party.metadata["gold"] == 50
        assert party.metadata["reputation"] == "good"


class TestPartySerialization:
    """Test party serialization for save/load."""

    def test_to_dict(self, hero, mage):
        """Test converting party to dictionary."""
        party = Party(name="Adventurers", members=[hero, mage], metadata={"gold": 100})
        data = party.to_dict()
        assert data["name"] == "Adventurers"
        assert len(data["member_ids"]) == 2
        assert hero.id in data["member_ids"]
        assert mage.id in data["member_ids"]
        assert data["metadata"]["gold"] == 100

    def test_from_dict(self, hero, mage):
        """Test creating party from dictionary."""
        data = {
            "name": "Adventurers",
            "member_ids": [hero.id, mage.id],
            "metadata": {"gold": 100},
        }
        entity_lookup = {hero.id: hero, mage.id: mage}
        party = Party.from_dict(data, entity_lookup)
        assert party.name == "Adventurers"
        assert party.size() == 2
        assert party.has_member(hero)
        assert party.has_member(mage)
        assert party.metadata["gold"] == 100

    def test_from_dict_missing_entities(self, hero, mage):
        """Test creating party when some entities aren't in lookup."""
        data = {
            "name": "Adventurers",
            "member_ids": [hero.id, mage.id, "unknown-id"],
            "metadata": {},
        }
        entity_lookup = {hero.id: hero}
        party = Party.from_dict(data, entity_lookup)
        assert party.size() == 1
        assert party.has_member(hero)
        assert not party.has_member(mage)


class TestCombatIntegration:
    """Test party integration with combat system."""

    def test_combat_with_party_objects(self, hero, mage, goblin, orc):
        """Test that Combat accepts Party objects."""
        player_party = Party(name="Heroes", members=[hero, mage])
        enemy_party = Party(name="Monsters", members=[goblin, orc])
        events = EventManager()

        combat = Combat(
            player_group=player_party, enemy_group=enemy_party, events=events
        )

        assert combat.players.members == [hero, mage]
        assert combat.enemies.members == [goblin, orc]

    def test_combat_with_lists_backward_compat(self, hero, mage, goblin):
        """Test that Combat still accepts lists (backward compatibility)."""
        events = EventManager()
        combat = Combat(player_group=[hero, mage], enemy_group=[goblin], events=events)

        assert combat.players.members == [hero, mage]
        assert combat.enemies.members == [goblin]

    def test_combat_with_mixed_types(self, hero, mage, goblin, orc):
        """Test that Combat can accept Party and list together."""
        player_party = Party(name="Heroes", members=[hero, mage])
        events = EventManager()

        combat = Combat(
            player_group=player_party, enemy_group=[goblin, orc], events=events
        )

        assert combat.players.members == [hero, mage]
        assert combat.enemies.members == [goblin, orc]

    def test_combat_lifecycle_with_party(self, hero, goblin):
        """Test full combat lifecycle with Party objects."""
        player_party = Party(name="Heroes", members=[hero])
        enemy_party = Party(name="Monsters", members=[goblin])
        events = EventManager()

        combat = Combat(
            player_group=player_party, enemy_group=enemy_party, events=events
        )

        combat.start()
        assert combat.is_active()

        current = combat.get_current_combatant()
        assert current in [hero, goblin]

    def test_party_persistence_after_combat(self, hero, mage, goblin):
        """Test that party object persists after combat."""
        party = Party(name="Heroes", members=[hero, mage])
        original_size = party.size()

        events = EventManager()
        combat = Combat(player_group=party, enemy_group=[goblin], events=events)
        combat.start()

        # Party object should still be intact
        assert party.size() == original_size
        assert party.has_member(hero)
        assert party.has_member(mage)

    def test_party_reflects_combat_damage(self, hero, goblin):
        """Test that damage in combat is reflected in party members."""
        party = Party(name="Heroes", members=[hero])
        initial_hp = hero.stats.hp

        events = EventManager()
        combat = Combat(player_group=party, enemy_group=[goblin], events=events)
        combat.start()

        # Manually damage hero
        hero.take_damage(20)

        # Party should reflect the change
        assert party.get_alive_members()[0].stats.hp < initial_hp

    def test_party_defeated_status_in_combat(self, hero, mage, goblin):
        """Test party defeated status during combat."""
        party = Party(name="Heroes", members=[hero, mage])

        events = EventManager()
        combat = Combat(player_group=party, enemy_group=[goblin], events=events)
        combat.start()

        # Kill all party members
        hero.stats.hp = 0
        mage.stats.hp = 0

        # Party should be defeated
        assert party.is_defeated()


class TestPartyExtensibility:
    """Test that Party can be extended for custom use cases."""

    def test_subclass_with_shared_gold(self, hero, mage):
        """Test subclassing Party to add shared resources."""

        class PartyWithGold(Party):
            shared_gold: int = 0

            def add_gold(self, amount: int):
                self.shared_gold += amount

            def spend_gold(self, amount: int) -> bool:
                if self.shared_gold >= amount:
                    self.shared_gold -= amount
                    return True
                return False

        party = PartyWithGold(name="Rich Adventurers", members=[hero, mage])
        party.add_gold(100)
        assert party.shared_gold == 100
        assert party.spend_gold(50) is True
        assert party.shared_gold == 50
        assert party.spend_gold(100) is False
        assert party.shared_gold == 50

    def test_subclass_with_formation(self, hero, mage, warrior):
        """Test subclassing Party to add formation system."""

        class PartyWithFormation(Party):
            formation: str = "standard"

            def set_formation(self, formation: str):
                self.formation = formation

            def get_front_line(self):
                # Front half of party
                return self.members[: len(self.members) // 2 + 1]

            def get_back_line(self):
                # Back half of party
                return self.members[len(self.members) // 2 + 1 :]

        party = PartyWithFormation(name="Tactical Squad", members=[warrior, hero, mage])
        party.set_formation("defensive")
        assert party.formation == "defensive"
        assert len(party.get_front_line()) == 2
        assert warrior in party.get_front_line()
        assert len(party.get_back_line()) == 1
        assert mage in party.get_back_line()
