"""Tests for damage type registry and resistance system."""

import pytest
import warnings
from barebones_rpg.combat.damage_types import DamageTypeManager, DamageTypeMetadata
from barebones_rpg.entities import Entity, Enemy, Stats


@pytest.fixture
def reset_registry():
    """Reset the manager before each test."""
    DamageTypeManager.reset()
    yield
    DamageTypeManager.reset()


class TestDamageTypeManager:
    """Tests for the DamageTypeManager."""

    def test_common_types_preregistered(self, reset_registry):
        """Test that common damage types are pre-registered."""
        common_types = [
            "physical",
            "magic",
            "fire",
            "ice",
            "poison",
            "lightning",
            "dark",
            "holy",
        ]
        for damage_type in common_types:
            assert DamageTypeManager().is_registered(damage_type)

    def test_register_custom_type(self, reset_registry):
        """Test registering a custom damage type."""
        DamageTypeManager().register(
            "necrotic", color="green", description="Death magic"
        )

        assert DamageTypeManager().is_registered("necrotic")
        metadata = DamageTypeManager().get_metadata("necrotic")
        assert metadata is not None
        assert metadata.name == "necrotic"
        assert metadata.color == "green"
        assert metadata.description == "Death magic"

    def test_register_with_tags(self, reset_registry):
        """Test registering with tags."""
        DamageTypeManager().register("arcane", tags=["magical", "rare"])

        metadata = DamageTypeManager().get_metadata("arcane")
        assert "magical" in metadata.tags
        assert "rare" in metadata.tags

    def test_register_with_custom_metadata(self, reset_registry):
        """Test registering with custom metadata fields."""
        DamageTypeManager().register(
            "quantum", special_effect="phase", power_level=9000
        )

        metadata = DamageTypeManager().get_metadata("quantum")
        assert metadata.custom["special_effect"] == "phase"
        assert metadata.custom["power_level"] == 9000

    def test_get_all_types(self, reset_registry):
        """Test getting all registered types."""
        all_types = DamageTypeManager().get_all()
        assert "physical" in all_types
        assert "fire" in all_types
        assert len(all_types) >= 8

    def test_get_all_with_metadata(self, reset_registry):
        """Test getting all types with metadata."""
        all_meta = DamageTypeManager().get_all_with_metadata()
        assert isinstance(all_meta, dict)
        assert isinstance(all_meta["fire"], DamageTypeMetadata)
        assert all_meta["fire"].color == "red"

    def test_lenient_mode_auto_registers(self, reset_registry):
        """Test that lenient mode auto-registers unknown types with warning."""
        DamageTypeManager().set_lenient_mode(True)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            DamageTypeManager().ensure_registered("unknown_type")
            assert len(w) == 1
            assert "Auto-registering" in str(w[0].message)

        assert DamageTypeManager().is_registered("unknown_type")

    def test_strict_mode_raises_error(self, reset_registry):
        """Test that strict mode raises error for unknown types."""
        DamageTypeManager().set_lenient_mode(False)

        with pytest.raises(ValueError, match="not registered"):
            DamageTypeManager().ensure_registered("unregistered_type")

    def test_ensure_registered_no_warning_for_existing(self, reset_registry):
        """Test that ensure_registered doesn't warn for already registered types."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            DamageTypeManager().ensure_registered("fire")
            assert len(w) == 0


class TestStatsResistances:
    """Tests for resistance methods in Stats."""

    def test_default_resistance_zero(self):
        """Test that default resistance is 0.0."""
        stats = Stats()
        assert stats.get_resistance("fire") == 0.0
        assert stats.get_resistance("unknown") == 0.0

    def test_set_resistance(self):
        """Test setting resistance."""
        stats = Stats()
        stats.set_resistance("fire", 0.5)
        assert stats.get_resistance("fire") == 0.5

    def test_modify_resistance(self):
        """Test modifying resistance."""
        stats = Stats()
        stats.set_resistance("fire", 0.3)
        stats.modify_resistance("fire", 0.2)
        assert stats.get_resistance("fire") == 0.5

    def test_negative_resistance_weakness(self):
        """Test that negative resistance represents weakness."""
        stats = Stats()
        stats.set_resistance("ice", -0.5)
        assert stats.get_resistance("ice") == -0.5

    def test_multiple_resistances(self):
        """Test managing multiple resistances."""
        stats = Stats(resistances={"fire": 0.75, "ice": 0.25, "poison": 0.5})
        assert stats.get_resistance("fire") == 0.75
        assert stats.get_resistance("ice") == 0.25
        assert stats.get_resistance("poison") == 0.5


class TestDamageCalculation:
    """Tests for damage calculation with resistances."""

    def test_no_resistance_no_defense(self, reset_registry):
        """Test damage with no resistance or defense."""
        entity = Entity(name="Test", stats=Stats(hp=100))
        damage = entity.take_damage(50, None, "fire")
        assert damage == 50
        assert entity.stats.hp == 50

    def test_with_resistance_only(self, reset_registry):
        """Test damage with resistance but no defense."""
        stats = Stats(hp=100, resistances={"fire": 0.5})
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 0 defense - (0.5 * 50) = 50 - 25 = 25
        damage = entity.take_damage(50, None, "fire")
        assert damage == 25
        assert entity.stats.hp == 75

    def test_with_defense_only(self, reset_registry):
        """Test damage with defense but no resistance."""
        stats = Stats(
            hp=100, base_physical_defense=10, constitution=0, defense_per_con=0
        )
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 10 defense - (0 * 50) = 40
        damage = entity.take_damage(50, None, "physical")
        assert damage == 40
        assert entity.stats.hp == 60

    def test_with_both_defense_and_resistance(self, reset_registry):
        """Test damage with both defense and resistance."""
        stats = Stats(
            hp=100,
            base_physical_defense=10,
            constitution=0,
            defense_per_con=0,
            resistances={"physical": 0.2},
        )
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 10 defense - (0.2 * 50) = 50 - 10 - 10 = 30
        damage = entity.take_damage(50, None, "physical")
        assert damage == 30
        assert entity.stats.hp == 70

    def test_weakness_increases_damage(self, reset_registry):
        """Test that negative resistance (weakness) increases damage."""
        stats = Stats(hp=100, resistances={"ice": -0.5})
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 0 defense - (-0.5 * 50) = 50 + 25 = 75
        damage = entity.take_damage(50, None, "ice")
        assert damage == 75
        assert entity.stats.hp == 25

    def test_full_resistance(self, reset_registry):
        """Test 100% resistance."""
        stats = Stats(hp=100, resistances={"fire": 1.0})
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 0 defense - (1.0 * 50) = 0
        damage = entity.take_damage(50, None, "fire")
        assert damage == 0
        assert entity.stats.hp == 100

    def test_over_100_percent_resistance(self, reset_registry):
        """Test that >100% resistance doesn't heal."""
        stats = Stats(hp=100, resistances={"fire": 1.5})
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 0 defense - (1.5 * 50) = -25, clamped to 0
        damage = entity.take_damage(50, None, "fire")
        assert damage == 0
        assert entity.stats.hp == 100

    def test_minimum_zero_damage(self, reset_registry):
        """Test that damage can't go negative."""
        stats = Stats(hp=100, base_physical_defense=100, resistances={"physical": 0.5})
        entity = Entity(name="Test", stats=stats)

        damage = entity.take_damage(50, None, "physical")
        assert damage == 0
        assert entity.stats.hp == 100

    def test_magic_defense_used_for_magic(self, reset_registry):
        """Test that magic defense is used for magic damage."""
        stats = Stats(
            hp=100, base_magic_defense=15, intelligence=0, magic_def_per_int=0
        )
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 15 magic_def - 0 = 35
        damage = entity.take_damage(50, None, "magic")
        assert damage == 35
        assert entity.stats.hp == 65

    def test_custom_type_no_defense(self, reset_registry):
        """Test that custom damage types don't use defense."""
        stats = Stats(hp=100, base_physical_defense=20, base_magic_defense=20)
        entity = Entity(name="Test", stats=stats)

        # Custom types ignore defense
        damage = entity.take_damage(50, None, "poison")
        assert damage == 50
        assert entity.stats.hp == 50

    def test_custom_type_with_resistance(self, reset_registry):
        """Test custom damage type with resistance."""
        stats = Stats(hp=100, base_physical_defense=20, resistances={"poison": 0.6})
        entity = Entity(name="Test", stats=stats)

        # 50 damage - 0 defense (custom type) - (0.6 * 50) = 50 - 30 = 20
        damage = entity.take_damage(50, None, "poison")
        assert damage == 20
        assert entity.stats.hp == 80


class TestEnemyWithResistances:
    """Tests for Enemy entities with resistances."""

    def test_enemy_fire_resistance(self, reset_registry):
        """Test creating an enemy with fire resistance."""
        fire_elemental = Enemy(
            name="Fire Elemental",
            stats=Stats(hp=100, resistances={"fire": 0.75, "ice": -0.5}),
        )

        # Fire damage (75% resist)
        fire_dmg = fire_elemental.take_damage(100, None, "fire")
        assert fire_dmg == 25

        # Ice damage (50% weakness)
        fire_elemental.stats.hp = 100
        ice_dmg = fire_elemental.take_damage(100, None, "ice")
        assert ice_dmg == 150

    def test_multiple_damage_types_in_sequence(self, reset_registry):
        """Test taking multiple damage types in sequence."""
        entity = Enemy(
            name="Mixed Resistant",
            stats=Stats(hp=200, resistances={"fire": 0.5, "ice": 0.3, "poison": 0.8}),
        )

        entity.take_damage(40, None, "fire")  # 20 damage
        assert entity.stats.hp == 180

        entity.take_damage(30, None, "ice")  # 21 damage
        assert entity.stats.hp == 159

        entity.take_damage(50, None, "poison")  # 10 damage
        assert entity.stats.hp == 149


class TestEdgeCases:
    """Tests for edge cases."""

    def test_zero_damage(self, reset_registry):
        """Test taking zero damage."""
        entity = Entity(name="Test", stats=Stats(hp=100))
        damage = entity.take_damage(0, None, "fire")
        assert damage == 0
        assert entity.stats.hp == 100

    def test_very_high_damage(self, reset_registry):
        """Test taking very high damage."""
        entity = Entity(name="Test", stats=Stats(hp=100))
        damage = entity.take_damage(999999, None, "physical")
        assert entity.stats.hp == 0
        assert entity.is_dead()

    def test_fractional_resistance(self, reset_registry):
        """Test fractional resistance values."""
        stats = Stats(hp=100, resistances={"fire": 0.333})
        entity = Entity(name="Test", stats=stats)

        # 100 damage - 0 defense - (0.333 * 100) = 100 - 33 = 67
        damage = entity.take_damage(100, None, "fire")
        assert damage == 67

    def test_resistance_on_low_damage(self, reset_registry):
        """Test resistance with low damage values."""
        stats = Stats(hp=100, resistances={"fire": 0.5})
        entity = Entity(name="Test", stats=stats)

        # 5 damage - 0 defense - (0.5 * 5) = 5 - 2 = 3 (int rounding)
        damage = entity.take_damage(5, None, "fire")
        assert damage == 3
