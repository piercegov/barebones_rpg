"""Singleton metaclass for framework systems.

This module provides a singleton pattern implementation for framework-managed
systems like QuestManager, ensuring only one instance exists.
"""

from typing import Dict, Any


class Singleton(type):
    """Metaclass that implements the singleton pattern.

    Ensures only one instance of a class exists. Subsequent calls to create
    an instance return the existing instance.

    Example:
        >>> class MySystem(metaclass=Singleton):
        ...     def __init__(self):
        ...         self.data = []
        >>>
        >>> instance1 = MySystem()
        >>> instance2 = MySystem()
        >>> instance1 is instance2
        True
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        """Create or return existing instance.

        Args:
            *args: Positional arguments for instance creation
            **kwargs: Keyword arguments for instance creation

        Returns:
            The singleton instance of the class
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def clear_instances(mcs):
        """Clear all singleton instances.

        Useful for testing or when you need to reset framework state.
        """
        mcs._instances.clear()
