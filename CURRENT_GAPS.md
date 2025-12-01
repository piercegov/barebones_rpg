# Current Gaps and Issues

This document tracks known gaps, issues, and areas for improvement in the Barebones RPG Framework.

---

## High Priority Issues

### ~~1. Incomplete Quest Loading~~ (RESOLVED)
- **Status**: Fixed - Quest loading now fully implemented via `QuestManager` as single source of truth
- **Changes**: `Game.load_game()` deserializes quests into `QuestManager`, rebuilds active/completed tracking lists from quest status. `game.register_quest()` deprecated in favor of `QuestManager().add_quest()`.

### ~~2. No Logging Framework~~ (RESOLVED)
- **Status**: Fixed - `game.py` and `save_manager.py` now use `logging.getLogger(__name__)`

### ~~3. Silent Failures in Loot System~~ (RESOLVED)
- **Status**: Fixed - `roll_loot_table()` now logs warnings via `logging.getLogger(__name__)` for all invalid loot entries
- **Changes**: Added `logger.warning()` calls for: non-dict entries, missing keys, invalid chance values, out-of-range chances, items not found in LootManager, and invalid item reference types

---

## Medium Priority Issues

### 3. Missing Test Coverage

| Area | Current State | Gap |
|------|---------------|-----|
| Rendering system | 0 tests | `pygame_renderer.py`, `ui_components.py`, `click_to_move.py` untested |
| ~~Data loaders~~ | ~~13 tests~~ | ~~Covered~~ - `DataLoader`, `ItemLoader`, `EntityLoader`, `DialogLoader`, `QuestLoader` |
| Events system | 9 tests | Missing tests for multiple subscribers, exception handling, event filtering |
| World system | 12 tests | Missing complex pathfinding and multi-location traversal tests |

### 4. Input Handling Stub
- **Location**: `barebones_rpg/core/game.py:265`
- **Issue**: `handle_input()` method is just a `pass` statement with comment "This will be implemented by the rendering layer"
- **Impact**: No framework-level input abstraction; rendering layer handles input directly without feeding back to Game
- **Fix**: Design and implement an input handling abstraction

### 5. No Custom Exceptions
- **Issue**: Framework uses generic exceptions everywhere
- **Impact**: Users cannot catch framework-specific errors; harder to distinguish between framework bugs and user errors
- **Fix**: Define custom exception classes (e.g., `CombatError`, `QuestError`, `SerializationError`)

### 6. StatusEffect Integration Incomplete
- **Location**: `barebones_rpg/entities/stats.py`
- **Issue**: `StatusEffect` class exists but:
  - No automatic removal after duration expires
  - Limited integration with combat actions
  - No built-in effect types (poison, stun, etc.)
- **Fix**: Add duration tracking and automatic expiration in combat/game loop

---

## Architecture Inconsistencies

### 7. Mixed Design Patterns
- **Singletons used**: `QuestManager`, `LootManager`, `DamageTypeManager`
- **Not singletons**: `Game`, `EventManager`, `SaveManager`
- **Unused**: `Registry[T]` base class defined but rarely used
- **Issue**: No clear criteria documented for when to use which pattern
- **Fix**: Document pattern selection criteria in CLAUDE.md

### ~~8. Type Hint Inconsistency~~ (RESOLVED)
- **Status**: Fixed - All type hints now use `typing` module (`List`, `Dict`, `Tuple`) consistently
- **Changes**: Standardized 9 files to use `from typing import ...` syntax instead of Python 3.10+ builtin lowercase syntax

### ~~9. Inconsistent Event Publishing Order~~ (RESOLVED)
- **Status**: Fixed - Standardized on "publish AFTER state change" pattern
- **Changes**:
  - `Combat._start_next_turn()`: State assignment moved before event publication
  - `Combat.end_turn()`: Turn advancement now happens before COMBAT_TURN_END event
  - `World.set_current_location()`: Location change happens before events; LOCATION_EXITED/ENTERED now include origin/destination
  - Added documentation in CLAUDE.md under "Event Publishing Order"

---

## Missing Features

### 10. Dialogue State Machine
- **Current**: Dialog system has linear navigation only
- **Missing**: State machine for complex branching, dialog variables/flags, loop/jump support
- **Workaround**: Users must manually construct complex dialog flows

### 11. Equipment System Gaps
- **Location**: `barebones_rpg/items/equipment.py`
- **Missing**:
  - Slot validation (prevent equipping sword in helmet slot)
  - Equipment requirements (level, class, stats)
  - Equipment set bonuses
- **Current**: Basic equip/unequip only

### 12. Party Shared Resources
- **Location**: `barebones_rpg/entities/party.py`
- **Missing**: Shared gold, shared inventory, resource pooling
- **Current**: Party only manages member list

### 13. Event Subscriber Cleanup
- **Location**: `barebones_rpg/core/events.py`
- **Issue**: No automatic cleanup of event subscribers
- **Impact**: Long-lived applications could accumulate subscribers; memory leak risk if objects register listeners but never unsubscribe
- **Fix**: Add weak references or explicit unsubscribe patterns

---

## Code Quality Issues

### 14. Weak Validation
- **Loot entries**: Silent `continue` on invalid data
- **Weapon range**: No validation that range >= 1 (can be negative)
- **Entity stats**: Minimal bounds checking

### 15. Missing Error Context
- **Location**: `barebones_rpg/core/game.py:329-360`
- **Issue**: Exception handling is too generic (catches all `Exception` types)
- **Fix**: Distinguish between error types and provide actionable messages

### 16. Callback Serialization Edge Cases
- **Location**: `barebones_rpg/core/serialization.py:96-106`
- **Issue**: When callbacks fail to register, only a warning is emitted; no exception handling if callback restoration fails during load
- **Impact**: Games can silently lose quest/item callbacks during save/load cycles

---

## Potential Runtime Issues

### 17. Circular Import Risk
- **Location**: `barebones_rpg/entities/entity.py:13-17`
- **Issue**: Uses `TYPE_CHECKING` to avoid circular imports; runtime fallback to `Any` could mask type errors

### 18. Singleton State Leakage in Tests
- **Issue**: All Singleton managers have `reset()` methods, but tests must explicitly call them
- **Impact**: If tests don't call `reset()`, state leaks between tests
- **Fix**: Document testing patterns; consider pytest fixtures that auto-reset

---

## Documentation Gaps

### 19. CLAUDE.md Missing Sections
- When to use Singleton vs Registry vs direct assignment
- Error handling best practices
- Testing patterns for Singleton reset
- Input handling architecture (since none exists)
- Quest loading limitations

---

## Summary

| Priority | Count | Key Items |
|----------|-------|-----------|
| High | 0 | All resolved |
| Medium | 4 | Test coverage, input handling, custom exceptions, StatusEffect |
| Architecture | 1 | Mixed patterns |
| Missing Features | 4 | Dialog state machine, equipment, party resources, event cleanup |
| Code Quality | 3 | Validation, error context, callback edge cases |

### Resolved
- ~~Logging framework~~ - Now uses `logging` module in `game.py` and `save_manager.py`
- ~~Quest loading~~ - Implemented via `QuestManager` as single source of truth
- ~~Silent loot failures~~ - Now logs warnings for invalid loot entries in `loot.py`
- ~~Data loader tests~~ - 13 tests covering all loader classes in `tests/test_loaders.py`
- ~~Type hint inconsistency~~ - Standardized on `typing` module throughout codebase
- ~~Event publishing order~~ - Standardized on "publish AFTER state change" pattern in combat and world systems

---

## Quick Wins

1. ~~Replace `print()` with `logging` module~~ (DONE)
2. ~~Add validation warnings to loot system~~ (DONE)
3. ~~Implement quest loading~~ (DONE - uses QuestManager)
4. ~~Add basic tests for loaders~~ (DONE - 13 tests in `test_loaders.py`)
5. ~~Standardize type hint style~~ (DONE - using `typing` module)
