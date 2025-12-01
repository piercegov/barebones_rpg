"""Tests for the custom exception hierarchy."""

import pytest

from barebones_rpg.core.exceptions import (
    BarebonesRPGError,
    UsageError,
    CombatError,
    QuestError,
    ItemError,
    EntityError,
    DialogError,
    WorldError,
    ConfigurationError,
    FrameworkError,
    SerializationError,
    InternalError,
)


class TestExceptionHierarchy:
    """Test that exceptions have the correct inheritance hierarchy."""

    def test_usage_error_is_barebones_error(self):
        """UsageError should be a subclass of BarebonesRPGError."""
        assert issubclass(UsageError, BarebonesRPGError)
        error = UsageError("test")
        assert isinstance(error, BarebonesRPGError)

    def test_framework_error_is_barebones_error(self):
        """FrameworkError should be a subclass of BarebonesRPGError."""
        assert issubclass(FrameworkError, BarebonesRPGError)
        error = FrameworkError("test")
        assert isinstance(error, BarebonesRPGError)

    def test_combat_error_hierarchy(self):
        """CombatError should be UsageError and BarebonesRPGError."""
        assert issubclass(CombatError, UsageError)
        assert issubclass(CombatError, BarebonesRPGError)
        error = CombatError("test")
        assert isinstance(error, UsageError)
        assert isinstance(error, BarebonesRPGError)

    def test_quest_error_hierarchy(self):
        """QuestError should be UsageError and BarebonesRPGError."""
        assert issubclass(QuestError, UsageError)
        error = QuestError("test")
        assert isinstance(error, UsageError)

    def test_item_error_hierarchy(self):
        """ItemError should be UsageError and BarebonesRPGError."""
        assert issubclass(ItemError, UsageError)
        error = ItemError("test")
        assert isinstance(error, UsageError)

    def test_entity_error_hierarchy(self):
        """EntityError should be UsageError and BarebonesRPGError."""
        assert issubclass(EntityError, UsageError)
        error = EntityError("test")
        assert isinstance(error, UsageError)

    def test_dialog_error_hierarchy(self):
        """DialogError should be UsageError and BarebonesRPGError."""
        assert issubclass(DialogError, UsageError)
        error = DialogError("test")
        assert isinstance(error, UsageError)

    def test_world_error_hierarchy(self):
        """WorldError should be UsageError and BarebonesRPGError."""
        assert issubclass(WorldError, UsageError)
        error = WorldError("test")
        assert isinstance(error, UsageError)

    def test_configuration_error_hierarchy(self):
        """ConfigurationError should be UsageError and BarebonesRPGError."""
        assert issubclass(ConfigurationError, UsageError)
        error = ConfigurationError("test")
        assert isinstance(error, UsageError)

    def test_serialization_error_hierarchy(self):
        """SerializationError should be FrameworkError and BarebonesRPGError."""
        assert issubclass(SerializationError, FrameworkError)
        assert issubclass(SerializationError, BarebonesRPGError)
        error = SerializationError("test")
        assert isinstance(error, FrameworkError)
        assert isinstance(error, BarebonesRPGError)

    def test_internal_error_hierarchy(self):
        """InternalError should be FrameworkError and BarebonesRPGError."""
        assert issubclass(InternalError, FrameworkError)
        error = InternalError("test")
        assert isinstance(error, FrameworkError)


class TestExceptionCatching:
    """Test that exceptions can be caught at appropriate levels."""

    def test_catch_all_framework_errors(self):
        """Should be able to catch all framework errors with BarebonesRPGError."""
        errors = [
            CombatError("test"),
            QuestError("test"),
            SerializationError("test"),
            InternalError("test"),
        ]
        for error in errors:
            try:
                raise error
            except BarebonesRPGError:
                pass  # Should catch all

    def test_catch_usage_errors_separately(self):
        """Should be able to catch UsageError without catching FrameworkError."""
        # UsageError should be caught
        try:
            raise CombatError("test")
        except UsageError:
            pass
        except FrameworkError:
            pytest.fail("CombatError should not be caught by FrameworkError")

        # FrameworkError should not be caught by UsageError
        with pytest.raises(SerializationError):
            try:
                raise SerializationError("test")
            except UsageError:
                pytest.fail("SerializationError should not be caught by UsageError")

    def test_catch_framework_errors_separately(self):
        """Should be able to catch FrameworkError without catching UsageError."""
        # FrameworkError should be caught
        try:
            raise SerializationError("test")
        except FrameworkError:
            pass
        except UsageError:
            pytest.fail("SerializationError should not be caught by UsageError")

    def test_error_message_preserved(self):
        """Error messages should be preserved."""
        message = "Something went wrong with combat"
        error = CombatError(message)
        assert str(error) == message

    def test_exception_chaining(self):
        """Exceptions should support chaining with 'from'."""
        original = ValueError("original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise SerializationError("wrapped error") from e
        except SerializationError as e:
            assert e.__cause__ is original
            assert "wrapped error" in str(e)


class TestExceptionUsageInFramework:
    """Test that exceptions are raised correctly by framework code."""

    def test_data_loader_raises_configuration_error(self):
        """DataLoader should raise ConfigurationError for unsupported formats."""
        from barebones_rpg.loaders.data_loader import DataLoader

        with pytest.raises(ConfigurationError) as exc_info:
            DataLoader.load_file("test.xml")

        assert "Unsupported file format" in str(exc_info.value)
        assert ".xml" in str(exc_info.value)

    def test_damage_type_manager_raises_combat_error(self):
        """DamageTypeManager should raise CombatError for unregistered types."""
        from barebones_rpg.combat.damage_types import DamageTypeManager

        manager = DamageTypeManager()
        manager.reset()  # Clear any existing state
        manager.set_lenient_mode(False)  # Strict mode

        with pytest.raises(CombatError) as exc_info:
            manager.ensure_registered("nonexistent_type")

        assert "not registered" in str(exc_info.value)

        # Cleanup
        manager.reset()

    def test_save_manager_raises_serialization_error_on_corrupt_json(self, tmp_path):
        """SaveManager should raise SerializationError for corrupt JSON."""
        from barebones_rpg.core.save_manager import SaveManager

        manager = SaveManager(str(tmp_path))

        # Create a corrupt save file
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{ this is not valid json }")

        with pytest.raises(SerializationError) as exc_info:
            manager.load("corrupt")

        assert "corrupted" in str(exc_info.value).lower() or "invalid JSON" in str(
            exc_info.value
        )

    def test_save_manager_raises_serialization_error_on_unserializable_data(
        self, tmp_path
    ):
        """SaveManager should raise SerializationError for non-serializable data."""
        from barebones_rpg.core.save_manager import SaveManager

        manager = SaveManager(str(tmp_path))

        # Try to save non-serializable data
        class NotSerializable:
            pass

        with pytest.raises(SerializationError) as exc_info:
            manager.save("test", {"bad_data": NotSerializable()})

        assert "non-serializable" in str(exc_info.value).lower() or "not JSON" in str(
            exc_info.value
        )
