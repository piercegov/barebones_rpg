"""Tests for serialization utilities."""

import pytest
from enum import Enum
from barebones_rpg.core.serialization import (
    CallbackRegistry,
    serialize_callback,
    deserialize_callback,
    serialize_callbacks,
    deserialize_callbacks,
    encode_enum,
    decode_enum,
    SerializationContext,
)
from barebones_rpg.entities.entity import Entity
from barebones_rpg.entities.stats import Stats
from barebones_rpg.items.item import Item, ItemType


class TestEnum(Enum):
    """Test enum for serialization testing."""

    VALUE_ONE = 1
    VALUE_TWO = 2
    VALUE_THREE = 3


def sample_callback(entity, context):
    """Sample callback for testing."""
    return "called"


def another_callback(entity, context):
    """Another callback for testing."""
    return "another"


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before and after each test."""
    CallbackRegistry.clear()
    yield
    CallbackRegistry.clear()


def test_callback_registry_register():
    """Test registering a callback."""
    CallbackRegistry.register("test_callback", sample_callback)

    assert CallbackRegistry.has("test_callback")
    assert CallbackRegistry.get("test_callback") is sample_callback


def test_callback_registry_get_nonexistent():
    """Test getting a non-existent callback returns None."""
    result = CallbackRegistry.get("nonexistent")
    assert result is None


def test_callback_registry_has():
    """Test checking if callback exists."""
    assert not CallbackRegistry.has("test_callback")

    CallbackRegistry.register("test_callback", sample_callback)
    assert CallbackRegistry.has("test_callback")


def test_callback_registry_encode_registered():
    """Test encoding a registered callback."""
    CallbackRegistry.register("my_callback", sample_callback)

    encoded = CallbackRegistry.encode(sample_callback)
    assert encoded == "my_callback"


def test_callback_registry_encode_none():
    """Test encoding None callback."""
    encoded = CallbackRegistry.encode(None)
    assert encoded is None


def test_callback_registry_encode_unregistered_auto_register():
    """Test encoding an unregistered callback auto-registers it."""
    with pytest.warns(UserWarning, match="not registered"):
        encoded = CallbackRegistry.encode(sample_callback)

    # Should auto-register with module.name format
    assert encoded is not None
    assert "sample_callback" in encoded
    assert CallbackRegistry.has(encoded)


def test_callback_registry_decode():
    """Test decoding a callback."""
    CallbackRegistry.register("test_callback", sample_callback)

    decoded = CallbackRegistry.decode("test_callback")
    assert decoded is sample_callback


def test_callback_registry_decode_none():
    """Test decoding None."""
    decoded = CallbackRegistry.decode(None)
    assert decoded is None


def test_callback_registry_decode_nonexistent():
    """Test decoding a non-existent callback."""
    decoded = CallbackRegistry.decode("nonexistent")
    assert decoded is None


def test_callback_registry_clear():
    """Test clearing the registry."""
    CallbackRegistry.register("callback1", sample_callback)
    CallbackRegistry.register("callback2", another_callback)

    assert CallbackRegistry.has("callback1")
    assert CallbackRegistry.has("callback2")

    CallbackRegistry.clear()

    assert not CallbackRegistry.has("callback1")
    assert not CallbackRegistry.has("callback2")


def test_callback_registry_get_all_names():
    """Test getting all callback names."""
    CallbackRegistry.register("callback1", sample_callback)
    CallbackRegistry.register("callback2", another_callback)

    names = CallbackRegistry.get_all_names()
    assert len(names) == 2
    assert "callback1" in names
    assert "callback2" in names


def test_callback_registry_auto_register_from_module():
    """Test auto-registering callbacks from a module."""
    # Register from a test module that has functions
    count = CallbackRegistry.auto_register_from_module("tests.test_serialization")

    # Should have registered at least our test functions
    assert count > 0


def test_callback_registry_auto_register_from_nonexistent_module():
    """Test auto-registering from non-existent module."""
    with pytest.warns(UserWarning, match="Could not import"):
        count = CallbackRegistry.auto_register_from_module("nonexistent.module")

    assert count == 0


def test_callback_registry_auto_register_with_prefix():
    """Test auto-registering with prefix."""
    count = CallbackRegistry.auto_register_from_module(
        "tests.test_serialization", prefix="test_"
    )

    assert count > 0
    # Check that at least one callback has the prefix
    names = CallbackRegistry.get_all_names()
    assert any(name.startswith("test_") for name in names)


def test_serialize_callback():
    """Test serialize_callback wrapper function."""
    CallbackRegistry.register("my_callback", sample_callback)

    result = serialize_callback(sample_callback)
    assert result == "my_callback"


def test_serialize_callback_none():
    """Test serialize_callback with None."""
    result = serialize_callback(None)
    assert result is None


def test_deserialize_callback():
    """Test deserialize_callback wrapper function."""
    CallbackRegistry.register("my_callback", sample_callback)

    result = deserialize_callback("my_callback")
    assert result is sample_callback


def test_deserialize_callback_none():
    """Test deserialize_callback with None."""
    result = deserialize_callback(None)
    assert result is None


def test_serialize_callbacks_list():
    """Test serializing a list of callbacks."""
    CallbackRegistry.register("callback1", sample_callback)
    CallbackRegistry.register("callback2", another_callback)

    callbacks = [sample_callback, another_callback]
    result = serialize_callbacks(callbacks)

    assert len(result) == 2
    assert "callback1" in result
    assert "callback2" in result


def test_serialize_callbacks_empty():
    """Test serializing empty callback list."""
    result = serialize_callbacks([])
    assert result == []


def test_serialize_callbacks_none():
    """Test serializing None callback list."""
    result = serialize_callbacks(None)
    assert result == []


def test_serialize_callbacks_with_none_values():
    """Test serializing callbacks with None values."""
    CallbackRegistry.register("callback1", sample_callback)

    callbacks = [sample_callback, None]
    result = serialize_callbacks(callbacks)

    # None values should be skipped
    assert len(result) == 1
    assert "callback1" in result


def test_deserialize_callbacks_list():
    """Test deserializing a list of callbacks."""
    CallbackRegistry.register("callback1", sample_callback)
    CallbackRegistry.register("callback2", another_callback)

    keys = ["callback1", "callback2"]
    result = deserialize_callbacks(keys)

    assert len(result) == 2
    assert sample_callback in result
    assert another_callback in result


def test_deserialize_callbacks_empty():
    """Test deserializing empty callback list."""
    result = deserialize_callbacks([])
    assert result == []


def test_deserialize_callbacks_none():
    """Test deserializing None callback list."""
    result = deserialize_callbacks(None)
    assert result == []


def test_deserialize_callbacks_with_unresolved():
    """Test deserializing callbacks with unresolved keys."""
    CallbackRegistry.register("callback1", sample_callback)

    keys = ["callback1", "nonexistent"]
    result = deserialize_callbacks(keys)

    # Unresolved keys should be skipped
    assert len(result) == 1
    assert sample_callback in result


def test_encode_enum():
    """Test encoding enum values."""
    result = encode_enum(TestEnum.VALUE_ONE)
    assert result == "VALUE_ONE"


def test_encode_enum_different_value():
    """Test encoding different enum value."""
    result = encode_enum(TestEnum.VALUE_THREE)
    assert result == "VALUE_THREE"


def test_encode_enum_with_no_name():
    """Test encoding value without name attribute."""
    result = encode_enum(42)
    assert result == "42"


def test_decode_enum():
    """Test decoding enum values."""
    result = decode_enum(TestEnum, "VALUE_ONE")
    assert result == TestEnum.VALUE_ONE


def test_decode_enum_different_value():
    """Test decoding different enum value."""
    result = decode_enum(TestEnum, "VALUE_TWO")
    assert result == TestEnum.VALUE_TWO


def test_serialization_context_initialization():
    """Test SerializationContext initialization."""
    context = SerializationContext()

    assert isinstance(context.entity_lookup, dict)
    assert isinstance(context.item_lookup, dict)
    assert isinstance(context.custom_serializers, dict)
    assert isinstance(context.custom_deserializers, dict)
    assert len(context.entity_lookup) == 0


def test_serialization_context_register_entity():
    """Test registering an entity in context."""
    context = SerializationContext()
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Entity(name="Test", stats=stats)

    context.register_entity(entity)

    assert entity.id in context.entity_lookup
    assert context.entity_lookup[entity.id] is entity


def test_serialization_context_register_entity_no_id():
    """Test registering an entity without id attribute."""
    context = SerializationContext()

    class EntityWithoutId:
        pass

    entity = EntityWithoutId()
    context.register_entity(entity)

    # Should not raise error, just not register
    assert len(context.entity_lookup) == 0


def test_serialization_context_get_entity():
    """Test getting an entity from context."""
    context = SerializationContext()
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity = Entity(name="Test", stats=stats)

    context.register_entity(entity)
    retrieved = context.get_entity(entity.id)

    assert retrieved is entity


def test_serialization_context_get_nonexistent_entity():
    """Test getting a non-existent entity."""
    context = SerializationContext()

    result = context.get_entity("nonexistent")
    assert result is None


def test_serialization_context_register_item():
    """Test registering an item in context."""
    context = SerializationContext()
    item = Item(name="Test Item", item_type=ItemType.MISC, value=10)

    context.register_item(item)

    assert item.id in context.item_lookup
    assert context.item_lookup[item.id] is item


def test_serialization_context_register_item_no_id():
    """Test registering an item without id attribute."""
    context = SerializationContext()

    class ItemWithoutId:
        pass

    item = ItemWithoutId()
    context.register_item(item)

    # Should not raise error, just not register
    assert len(context.item_lookup) == 0


def test_serialization_context_get_item():
    """Test getting an item from context."""
    context = SerializationContext()
    item = Item(name="Test Item", item_type=ItemType.MISC, value=10)

    context.register_item(item)
    retrieved = context.get_item(item.id)

    assert retrieved is item


def test_serialization_context_get_nonexistent_item():
    """Test getting a non-existent item."""
    context = SerializationContext()

    result = context.get_item("nonexistent")
    assert result is None


def test_serialization_context_multiple_entities():
    """Test registering multiple entities."""
    context = SerializationContext()
    stats = Stats(
        strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
    )
    entity1 = Entity(name="Entity1", stats=stats)
    entity2 = Entity(name="Entity2", stats=stats)

    context.register_entity(entity1)
    context.register_entity(entity2)

    assert len(context.entity_lookup) == 2
    assert context.get_entity(entity1.id) is entity1
    assert context.get_entity(entity2.id) is entity2


def test_serialization_context_multiple_items():
    """Test registering multiple items."""
    context = SerializationContext()
    item1 = Item(name="Item1", item_type=ItemType.MISC, value=10)
    item2 = Item(name="Item2", item_type=ItemType.MISC, value=20)

    context.register_item(item1)
    context.register_item(item2)

    assert len(context.item_lookup) == 2
    assert context.get_item(item1.id) is item1
    assert context.get_item(item2.id) is item2
