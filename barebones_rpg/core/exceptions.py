"""Custom exceptions for the Barebones RPG Framework.

This module defines a hierarchy of exceptions that help users distinguish
between their own mistakes (UsageError and subclasses) and internal
framework problems (FrameworkError and subclasses).

Exception Hierarchy:
    BarebonesRPGError (base)
    ├── UsageError (user misusing the framework)
    │   ├── CombatError
    │   ├── QuestError
    │   ├── ItemError
    │   ├── EntityError
    │   ├── DialogError
    │   ├── WorldError
    │   └── ConfigurationError
    └── FrameworkError (internal framework problems)
        ├── SerializationError
        └── InternalError

Example:
    >>> from barebones_rpg.core.exceptions import CombatError, UsageError
    >>> try:
    ...     # some combat operation
    ...     raise CombatError("Cannot attack during dialog state")
    ... except UsageError as e:
    ...     print(f"User error: {e}")
    ... except FrameworkError as e:
    ...     print(f"Framework bug: {e}")
"""


class BarebonesRPGError(Exception):
    """Base exception for all Barebones RPG framework exceptions.

    All exceptions raised by the framework inherit from this class,
    allowing users to catch all framework exceptions with a single
    except clause if desired.

    Example:
        >>> try:
        ...     # framework operations
        ... except BarebonesRPGError as e:
        ...     print(f"Framework error: {e}")
    """

    pass


# =============================================================================
# Usage Errors - User is misusing the framework
# =============================================================================


class UsageError(BarebonesRPGError):
    """Base class for errors caused by incorrect framework usage.

    Raised when the user is using the framework incorrectly. This could be
    calling methods in the wrong order, passing invalid parameters, or
    attempting operations that aren't allowed in the current state.

    Users should catch this to handle their own mistakes gracefully.
    """

    pass


class CombatError(UsageError):
    """Combat-related usage error.

    Raised when combat operations are used incorrectly, such as:
    - Attempting combat actions outside of combat
    - Using unregistered damage types in strict mode
    - Invalid target selection
    - Actions that violate combat rules

    Example:
        >>> raise CombatError("Cannot attack: not in combat state")
    """

    pass


class QuestError(UsageError):
    """Quest-related usage error.

    Raised when quest operations are used incorrectly, such as:
    - Completing objectives out of order
    - Starting already-active quests
    - Invalid quest state transitions

    Example:
        >>> raise QuestError("Quest 'main_quest' is already completed")
    """

    pass


class ItemError(UsageError):
    """Item, inventory, or loot-related usage error.

    Raised when item operations are used incorrectly, such as:
    - Equipping items to invalid slots
    - Using items that can't be used
    - Invalid inventory operations
    - Loot table configuration errors

    Example:
        >>> raise ItemError("Cannot equip 'sword' in HEAD slot")
    """

    pass


class EntityError(UsageError):
    """Entity-related usage error.

    Raised when entity operations are used incorrectly, such as:
    - Invalid stat modifications
    - Operations on dead entities
    - Invalid entity state transitions

    Example:
        >>> raise EntityError("Cannot add experience to dead entity")
    """

    pass


class DialogError(UsageError):
    """Dialog system usage error.

    Raised when dialog operations are used incorrectly, such as:
    - Invalid dialog node references
    - Selecting unavailable choices
    - Dialog state machine violations

    Example:
        >>> raise DialogError("Choice index 5 out of range (0-2)")
    """

    pass


class WorldError(UsageError):
    """World and location usage error.

    Raised when world/location operations are used incorrectly, such as:
    - Moving to non-existent locations
    - Invalid pathfinding requests
    - Location connection errors

    Example:
        >>> raise WorldError("Location 'dungeon_2' not connected to current location")
    """

    pass


class ConfigurationError(UsageError):
    """Configuration or setup error.

    Raised when the framework is configured incorrectly, such as:
    - Invalid file formats for data loading
    - Missing required configuration
    - Invalid game setup

    Example:
        >>> raise ConfigurationError("Unsupported file format: .xml")
    """

    pass


# =============================================================================
# Framework Errors - Something went wrong internally
# =============================================================================


class FrameworkError(BarebonesRPGError):
    """Base class for internal framework errors.

    Raised when something goes wrong inside the framework that isn't
    the user's fault. These indicate bugs or unexpected conditions
    in the framework itself.

    Users should catch this to handle framework failures gracefully,
    and ideally report them as bugs.
    """

    pass


class SerializationError(FrameworkError):
    """Save/load operation failure.

    Raised when serialization or deserialization fails, such as:
    - Corrupted save files
    - Version incompatibilities
    - Failed callback restoration
    - JSON parsing errors

    Example:
        >>> raise SerializationError("Failed to load save file: invalid JSON")
    """

    pass


class InternalError(FrameworkError):
    """Unexpected internal framework failure.

    Raised when an unexpected condition occurs inside the framework.
    This typically indicates a bug in the framework.

    Example:
        >>> raise InternalError("Unexpected state in combat loop")
    """

    pass
