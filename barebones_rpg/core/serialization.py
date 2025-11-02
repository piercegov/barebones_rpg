"""Serialization utilities for save/load system.

This module provides utilities for serializing game state, including a callback
registry for handling function references in saved data.
"""

from typing import Callable, Dict, Any, Optional, List, Union, Type
from enum import Enum
import importlib
import warnings


class CallbackRegistry:
    """Registry for mapping callback functions to symbolic names.

    This enables serialization of callbacks by storing symbolic names instead
    of function references. When loading, the registry is used to restore
    the actual function references.

    Example:
        >>> def heal_player(entity, context):
        ...     entity.heal(50)
        >>>
        >>> CallbackRegistry.register("heal_player", heal_player)
        >>> key = CallbackRegistry.encode(heal_player)
        >>> print(key)
        'heal_player'
        >>>
        >>> restored = CallbackRegistry.decode(key)
        >>> restored is heal_player
        True
    """

    _registry: Dict[str, Callable] = {}
    _reverse_lookup: Dict[int, str] = {}  # id(func) -> name

    @classmethod
    def register(cls, name: str, callback: Callable) -> None:
        """Register a callback with a symbolic name.

        Args:
            name: Symbolic name for the callback
            callback: The callback function to register

        Example:
            >>> CallbackRegistry.register("my_callback", my_function)
        """
        cls._registry[name] = callback
        cls._reverse_lookup[id(callback)] = name

    @classmethod
    def get(cls, name: str) -> Optional[Callable]:
        """Get a callback by name.

        Args:
            name: Name of the callback

        Returns:
            The callback function or None if not found
        """
        return cls._registry.get(name)

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a callback is registered.

        Args:
            name: Name to check

        Returns:
            True if callback is registered
        """
        return name in cls._registry

    @classmethod
    def encode(cls, callback: Optional[Callable]) -> Optional[str]:
        """Encode a callback to its symbolic name.

        Args:
            callback: The callback function to encode

        Returns:
            Symbolic name or None if callback is None or not registered

        Example:
            >>> key = CallbackRegistry.encode(my_function)
        """
        if callback is None:
            return None

        callback_id = id(callback)
        if callback_id in cls._reverse_lookup:
            return cls._reverse_lookup[callback_id]

        # Try to auto-register if it has a __name__ and __module__
        if hasattr(callback, "__name__") and hasattr(callback, "__module__"):
            auto_name = f"{callback.__module__}.{callback.__name__}"
            warnings.warn(
                f"Callback '{auto_name}' not registered. Auto-registering. "
                f"Consider pre-registering with CallbackRegistry.register()",
                UserWarning,
                stacklevel=2,
            )
            cls.register(auto_name, callback)
            return auto_name

        return None

    @classmethod
    def decode(cls, name: Optional[str]) -> Optional[Callable]:
        """Decode a symbolic name back to a callback.

        Args:
            name: Symbolic name of the callback

        Returns:
            The callback function or None if not found

        Example:
            >>> callback = CallbackRegistry.decode("my_callback")
        """
        if name is None:
            return None
        return cls.get(name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered callbacks.

        This is primarily for testing purposes.
        """
        cls._registry.clear()
        cls._reverse_lookup.clear()

    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get all registered callback names.

        Returns:
            List of callback names
        """
        return list(cls._registry.keys())

    @classmethod
    def auto_register_from_module(cls, module_name: str, prefix: str = "") -> int:
        """Auto-register all functions from a module.

        This is a convenience method for bulk registration.

        Args:
            module_name: Name of the module to import
            prefix: Optional prefix for registered names

        Returns:
            Number of functions registered

        Example:
            >>> CallbackRegistry.auto_register_from_module("my_game.callbacks")
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            warnings.warn(f"Could not import module '{module_name}'", UserWarning)
            return 0

        count = 0
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                name = f"{prefix}{attr_name}" if prefix else attr_name
                cls.register(name, attr)
                count += 1

        return count


def serialize_callback(callback: Optional[Callable]) -> Optional[str]:
    """Serialize a callback to a string key.

    This is a convenience wrapper around CallbackRegistry.encode().

    Args:
        callback: Callback to serialize

    Returns:
        String key or None
    """
    return CallbackRegistry.encode(callback)


def deserialize_callback(key: Optional[str]) -> Optional[Callable]:
    """Deserialize a callback from a string key.

    This is a convenience wrapper around CallbackRegistry.decode().

    Args:
        key: String key to deserialize

    Returns:
        Callback function or None
    """
    return CallbackRegistry.decode(key)


def serialize_callbacks(callbacks: Optional[List[Callable]]) -> List[str]:
    """Serialize a list of callbacks.

    Args:
        callbacks: List of callbacks to serialize

    Returns:
        List of string keys (skips None values)
    """
    if not callbacks:
        return []

    result = []
    for callback in callbacks:
        key = serialize_callback(callback)
        if key is not None:
            result.append(key)
    return result


def deserialize_callbacks(keys: Optional[List[str]]) -> List[Callable]:
    """Deserialize a list of callbacks.

    Args:
        keys: List of string keys

    Returns:
        List of callback functions (skips unresolved keys)
    """
    if not keys:
        return []

    result = []
    for key in keys:
        callback = deserialize_callback(key)
        if callback is not None:
            result.append(callback)
    return result


def encode_enum(enum_value: Any) -> str:
    """Encode an enum value to a string.

    Args:
        enum_value: Enum value to encode

    Returns:
        String representation (enum.name)
    """
    if hasattr(enum_value, "name"):
        return enum_value.name
    return str(enum_value)


def decode_enum(enum_class: Type[Enum], value: str) -> Any:
    """Decode a string to an enum value.

    Args:
        enum_class: The enum class
        value: String name of the enum value

    Returns:
        Enum value
    """
    return enum_class[value]


class SerializationContext:
    """Context for serialization operations.

    This can be used to pass additional context during serialization,
    such as entity lookups, custom serializers, etc.
    """

    def __init__(self):
        self.entity_lookup: Dict[str, Any] = {}
        self.item_lookup: Dict[str, Any] = {}
        self.custom_serializers: Dict[type, Callable] = {}
        self.custom_deserializers: Dict[str, Callable] = {}

    def register_entity(self, entity: Any) -> None:
        """Register an entity for lookup during deserialization.

        Args:
            entity: Entity to register
        """
        if hasattr(entity, "id"):
            self.entity_lookup[entity.id] = entity

    def register_item(self, item: Any) -> None:
        """Register an item for lookup during deserialization.

        Args:
            item: Item to register
        """
        if hasattr(item, "id"):
            self.item_lookup[item.id] = item

    def get_entity(self, entity_id: str) -> Optional[Any]:
        """Get an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self.entity_lookup.get(entity_id)

    def get_item(self, item_id: str) -> Optional[Any]:
        """Get an item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item or None if not found
        """
        return self.item_lookup.get(item_id)
