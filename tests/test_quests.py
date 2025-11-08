"""Tests for the quest system."""

import pytest
from barebones_rpg.quests.quest import (
    Quest,
    QuestObjective,
    QuestStatus,
    ObjectiveType,
    QuestManager,
)
from barebones_rpg.core.events import EventManager, EventType


@pytest.fixture(autouse=True)
def reset_quest_manager():
    """Reset QuestManager singleton before each test."""
    QuestManager.reset()
    yield
    QuestManager.reset()


def test_objective_increment_beyond_target_marks_complete():
    """Incrementing objective beyond target_count should mark it complete."""
    objective = QuestObjective(
        description="Collect 5 items",
        objective_type=ObjectiveType.COLLECT_ITEM,
        target="Gold Coin",
        target_count=5,
        current_count=0,
    )

    objective.increment(10)

    assert objective.completed is True
    assert objective.current_count == 10


def test_quest_completes_when_all_objectives_complete():
    """Quest should complete when all objectives are completed."""
    events = EventManager()
    events.enable_history()

    quest = Quest(name="Test Quest", description="Test")

    obj1 = QuestObjective(
        description="Objective 1", objective_type=ObjectiveType.CUSTOM, target_count=1
    )
    obj2 = QuestObjective(
        description="Objective 2", objective_type=ObjectiveType.CUSTOM, target_count=1
    )

    quest.add_objective(obj1)
    quest.add_objective(obj2)

    quest.start(events)

    obj1.increment(1)
    obj2.increment(1)

    quest.check_completion(events)

    assert quest.is_completed()


def test_quest_manager_tracks_active_vs_completed():
    """QuestManager should track active vs completed quests."""
    events = EventManager()
    manager = QuestManager()

    quest = Quest(name="Test Quest")
    objective = QuestObjective(
        description="Test objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
    )
    quest.add_objective(objective)

    # Explicitly add quest to manager (no longer auto-registered)
    manager.add_quest(quest)

    manager.start_quest(quest.id, events)

    assert quest.id in manager.active_quests
    assert quest.id not in manager.completed_quests

    objective.increment(1)
    manager.complete_quest(quest.id, events)

    assert quest.id not in manager.active_quests
    assert quest.id in manager.completed_quests


def test_objective_progress_with_custom_conditions():
    """Objectives with custom conditions can override the standard count-based completion."""
    condition_met = {"value": False}

    def custom_condition(obj):
        return condition_met["value"]

    objective = QuestObjective(
        description="Custom objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=10,
        condition=custom_condition,
    )

    objective.increment(5)

    assert objective.completed is False
    assert not objective.is_completed()

    condition_met["value"] = True

    assert objective.is_completed()


def test_quest_status_transitions():
    """Quest should transition through status states correctly."""
    events = EventManager()
    quest = Quest(name="Test Quest")
    objective = QuestObjective(
        description="Test objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
    )
    quest.add_objective(objective)

    # Explicitly add quest to manager (no longer auto-registered)
    QuestManager().add_quest(quest)

    assert quest.status == QuestStatus.NOT_STARTED

    quest.start(events)
    assert quest.status == QuestStatus.ACTIVE

    objective.increment(1)
    quest.check_completion(events)
    assert quest.status == QuestStatus.COMPLETED


def test_quest_fail_transition():
    """Quest should be able to fail."""
    events = EventManager()
    quest = Quest(name="Test Quest")
    objective = QuestObjective(
        description="Test objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
    )
    quest.add_objective(objective)

    quest.start(events)
    assert quest.status == QuestStatus.ACTIVE

    quest.fail(events)
    assert quest.status == QuestStatus.FAILED


def test_multiple_objectives_same_type_different_targets():
    """Multiple objectives of same type with different targets should work."""
    events = EventManager()
    quest = Quest(name="Hunt Quest")

    obj1 = QuestObjective(
        description="Kill 5 goblins",
        objective_type=ObjectiveType.KILL_ENEMY,
        target="Goblin",
        target_count=5,
    )
    obj2 = QuestObjective(
        description="Kill 3 orcs",
        objective_type=ObjectiveType.KILL_ENEMY,
        target="Orc",
        target_count=3,
    )

    quest.add_objective(obj1)
    quest.add_objective(obj2)

    assert len(quest.objectives) == 2
    assert obj1.target != obj2.target


def test_event_publishing_for_quest_milestones():
    """Events should be published for quest and objective milestones."""
    events = EventManager()
    events.enable_history()

    quest = Quest(name="Test Quest")
    objective = QuestObjective(
        description="Test objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
    )
    quest.add_objective(objective)

    quest.start(events)

    history = events.get_history()
    quest_started = [e for e in history if e.event_type == EventType.QUEST_STARTED]
    assert len(quest_started) == 1

    objective.increment(1)

    quest.check_completion(events)

    history = events.get_history()
    quest_completed = [e for e in history if e.event_type == EventType.QUEST_COMPLETED]
    assert len(quest_completed) == 1


def test_objective_on_complete_callback():
    """Objective on_complete callback should execute when objective completes."""
    callback_executed = {"executed": False}

    def on_complete(obj):
        callback_executed["executed"] = True

    objective = QuestObjective(
        description="Test",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
        on_complete=on_complete,
    )

    objective.increment(1)

    assert callback_executed["executed"] is True


def test_objective_on_progress_callback():
    """Objective on_progress callback should execute on increment."""
    progress_count = {"count": 0}

    def on_progress(obj):
        progress_count["count"] += 1

    objective = QuestObjective(
        description="Test",
        objective_type=ObjectiveType.CUSTOM,
        target_count=5,
        on_progress=on_progress,
    )

    objective.increment(1)
    objective.increment(1)

    assert progress_count["count"] == 2


def test_quest_manager_update_objective():
    """QuestManager update_objective should update matching objectives."""
    events = EventManager()
    manager = QuestManager()

    quest = Quest(name="Hunt Quest")
    objective = QuestObjective(
        description="Kill goblins",
        objective_type=ObjectiveType.KILL_ENEMY,
        target="Goblin",
        target_count=5,
    )
    quest.add_objective(objective)

    # Explicitly add quest to manager (no longer auto-registered)
    manager.add_quest(quest)

    manager.start_quest(quest.id, events)

    updated = manager.update_objective(
        quest.id, ObjectiveType.KILL_ENEMY, "Goblin", 2, events
    )

    assert updated is True
    assert objective.current_count == 2


def test_quest_manager_get_active_quests():
    """QuestManager should return list of active quests."""
    events = EventManager()
    manager = QuestManager()

    quest1 = Quest(name="Quest 1")
    quest2 = Quest(name="Quest 2")

    # Explicitly add quests to manager (no longer auto-registered)
    manager.add_quest(quest1)
    manager.add_quest(quest2)

    manager.start_quest(quest1.id, events)
    manager.start_quest(quest2.id, events)

    active = manager.get_active_quests()

    assert len(active) == 2
    assert quest1 in active
    assert quest2 in active


def test_quest_manager_get_quest_by_name():
    """QuestManager should find quests by name."""
    manager = QuestManager()

    quest = Quest(name="Unique Quest Name")

    # Explicitly add quest to manager (no longer auto-registered)
    manager.add_quest(quest)

    found = manager.get_quest_by_name("Unique Quest Name")

    assert found is not None
    assert found.id == quest.id


def test_objective_get_progress_text():
    """Objective should return progress text."""
    objective = QuestObjective(
        description="Test",
        objective_type=ObjectiveType.CUSTOM,
        current_count=3,
        target_count=10,
    )

    progress = objective.get_progress_text()

    assert progress == "3/10"


def test_quest_get_progress_percentage():
    """Quest should calculate overall progress percentage."""
    quest = Quest(name="Test Quest")

    obj1 = QuestObjective(
        description="Obj 1", objective_type=ObjectiveType.CUSTOM, target_count=1
    )
    obj2 = QuestObjective(
        description="Obj 2", objective_type=ObjectiveType.CUSTOM, target_count=1
    )
    obj3 = QuestObjective(
        description="Obj 3", objective_type=ObjectiveType.CUSTOM, target_count=1
    )

    quest.add_objective(obj1)
    quest.add_objective(obj2)
    quest.add_objective(obj3)

    obj1.increment(1)

    progress = quest.get_progress_percentage()

    assert progress == pytest.approx(1.0 / 3.0)


def test_quest_is_active():
    """Quest is_active should return correct status."""
    events = EventManager()
    quest = Quest(name="Test Quest")
    objective = QuestObjective(
        description="Test objective",
        objective_type=ObjectiveType.CUSTOM,
        target_count=1,
    )
    quest.add_objective(objective)

    assert not quest.is_active()

    quest.start(events)

    assert quest.is_active()


def test_quest_manager_singleton():
    """QuestManager should be a singleton."""
    manager1 = QuestManager()
    manager2 = QuestManager()

    assert manager1 is manager2


def test_quest_explicit_registration_to_manager():
    """Quest should be explicitly registered to QuestManager."""
    manager = QuestManager()

    quest = Quest(name="Explicitly-registered Quest")

    # Quest should NOT be auto-registered
    found_before = manager.get_quest(quest.id)
    assert found_before is None

    # Explicitly add quest to manager
    manager.add_quest(quest)

    # Now it should be found
    found_after = manager.get_quest(quest.id)
    assert found_after is not None
    assert found_after.id == quest.id
