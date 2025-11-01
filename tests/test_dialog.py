"""Tests for the dialog system."""

import pytest
from barebones_rpg.dialog.dialog import (
    DialogTree,
    DialogNode,
    DialogChoice,
    DialogSession,
)


def test_dialog_tree_validation_catches_missing_start_node():
    """DialogTree validation should catch missing start nodes."""
    tree = DialogTree(name="Test Tree")

    errors = tree.validate_tree()

    assert len(errors) > 0
    assert any("start node" in error.lower() for error in errors)


def test_dialog_tree_validation_catches_missing_referenced_nodes():
    """DialogTree validation should catch references to non-existent nodes."""
    tree = DialogTree(name="Test Tree")

    node = DialogNode(
        id="start",
        text="Hello",
        choices=[DialogChoice(text="Go to missing", next_node_id="nonexistent")],
    )
    tree.add_node(node)
    tree.set_start_node("start")

    errors = tree.validate_tree()

    assert len(errors) > 0
    assert any("nonexistent" in error for error in errors)


def test_dialog_tree_validation_passes_for_valid_tree():
    """Valid dialog tree should pass validation."""
    tree = DialogTree(name="Test Tree")

    start_node = DialogNode(
        id="start",
        text="Hello",
        choices=[DialogChoice(text="Next", next_node_id="end")],
    )
    end_node = DialogNode(id="end", text="Goodbye", choices=[])

    tree.add_node(start_node)
    tree.add_node(end_node)
    tree.set_start_node("start")

    errors = tree.validate_tree()

    assert len(errors) == 0


def test_choices_with_conditions_are_filtered():
    """Choices with conditions should be filtered based on context."""
    context = {"has_key": True}

    choice_always = DialogChoice(text="Always available", next_node_id="node1")
    choice_conditional = DialogChoice(
        text="Need key",
        next_node_id="node2",
        condition=lambda ctx: ctx.get("has_key", False),
    )
    choice_not_available = DialogChoice(
        text="Need sword",
        next_node_id="node3",
        condition=lambda ctx: ctx.get("has_sword", False),
    )

    node = DialogNode(
        id="test",
        text="Test node",
        choices=[choice_always, choice_conditional, choice_not_available],
    )

    available = node.get_available_choices(context)

    assert len(available) == 2
    assert choice_always in available
    assert choice_conditional in available
    assert choice_not_available not in available


def test_dialog_session_navigation_handles_end():
    """DialogSession should handle end-of-dialog (next_node_id=None)."""
    tree = DialogTree(name="Test Tree")

    start_node = DialogNode(
        id="start", text="Hello", choices=[DialogChoice(text="End", next_node_id=None)]
    )
    tree.add_node(start_node)
    tree.set_start_node("start")

    session = DialogSession(tree)
    session.start()

    assert session.is_active

    next_node = session.make_choice(0)

    assert next_node is None
    assert not session.is_active


def test_making_invalid_choice_index():
    """Making an invalid choice index should return None."""
    tree = DialogTree(name="Test Tree")

    start_node = DialogNode(
        id="start",
        text="Hello",
        choices=[DialogChoice(text="Option 1", next_node_id="node1")],
    )
    tree.add_node(start_node)
    tree.set_start_node("start")

    session = DialogSession(tree)
    session.start()

    result = session.make_choice(999)

    assert result is None


def test_node_enter_exit_callbacks_execute():
    """Node enter and exit callbacks should execute in correct order."""
    execution_order = []

    def on_enter_start(ctx):
        execution_order.append("enter_start")

    def on_exit_start(ctx):
        execution_order.append("exit_start")

    def on_enter_next(ctx):
        execution_order.append("enter_next")

    tree = DialogTree(name="Test Tree")

    start_node = DialogNode(
        id="start",
        text="Start",
        choices=[DialogChoice(text="Next", next_node_id="next")],
        on_enter=on_enter_start,
        on_exit=on_exit_start,
    )
    next_node = DialogNode(id="next", text="Next", choices=[], on_enter=on_enter_next)

    tree.add_node(start_node)
    tree.add_node(next_node)
    tree.set_start_node("start")

    session = DialogSession(tree)
    session.start()

    assert execution_order == ["enter_start"]

    session.make_choice(0)

    assert execution_order == ["enter_start", "exit_start", "enter_next"]


def test_dialog_choice_callbacks_execute():
    """DialogChoice callbacks should execute when choice is selected."""
    callback_executed = {"executed": False}

    def on_select(ctx):
        callback_executed["executed"] = True
        return "callback_result"

    tree = DialogTree(name="Test Tree")

    start_node = DialogNode(
        id="start",
        text="Start",
        choices=[DialogChoice(text="Click me", next_node_id=None, on_select=on_select)],
    )
    tree.add_node(start_node)
    tree.set_start_node("start")

    session = DialogSession(tree)
    session.start()
    session.make_choice(0)

    assert callback_executed["executed"] is True


def test_dialog_session_tracks_history():
    """DialogSession should track the history of visited nodes."""
    tree = DialogTree(name="Test Tree")

    node1 = DialogNode(
        id="node1",
        text="First",
        choices=[DialogChoice(text="Next", next_node_id="node2")],
    )
    node2 = DialogNode(
        id="node2",
        text="Second",
        choices=[DialogChoice(text="Next", next_node_id="node3")],
    )
    node3 = DialogNode(id="node3", text="Third", choices=[])

    tree.add_node(node1)
    tree.add_node(node2)
    tree.add_node(node3)
    tree.set_start_node("node1")

    session = DialogSession(tree)
    session.start()

    assert len(session.history) == 1
    assert session.history[0] == "node1"

    session.make_choice(0)
    assert len(session.history) == 2
    assert session.history[1] == "node2"

    session.make_choice(0)
    assert len(session.history) == 3
    assert session.history[2] == "node3"


def test_dialog_tree_auto_sets_first_node_as_start():
    """Adding first node should auto-set it as start node."""
    tree = DialogTree(name="Test Tree")

    node = DialogNode(id="first", text="First node")
    tree.add_node(node)

    assert tree.start_node_id == "first"


def test_dialog_session_get_current_node():
    """get_current_node should return the active node."""
    tree = DialogTree(name="Test Tree")

    node = DialogNode(id="start", text="Hello", choices=[])
    tree.add_node(node)

    session = DialogSession(tree)
    session.start()

    current = session.get_current_node()

    assert current is not None
    assert current.id == "start"


def test_dialog_session_get_available_choices():
    """get_available_choices should return available choices at current node."""
    tree = DialogTree(name="Test Tree")

    node = DialogNode(
        id="start",
        text="Hello",
        choices=[
            DialogChoice(text="Option 1", next_node_id="node1"),
            DialogChoice(text="Option 2", next_node_id="node2"),
        ],
    )
    tree.add_node(node)
    tree.set_start_node("start")

    session = DialogSession(tree)
    session.start()

    choices = session.get_available_choices()

    assert len(choices) == 2


def test_dialog_choice_is_available_without_condition():
    """Choices without conditions should always be available."""
    choice = DialogChoice(text="Always available", next_node_id="node1")

    assert choice.is_available({}) is True
    assert choice.is_available({"any": "context"}) is True


def test_dialog_session_end_explicitly():
    """Calling end() should end the dialog session."""
    tree = DialogTree(name="Test Tree")

    node = DialogNode(id="start", text="Hello")
    tree.add_node(node)

    session = DialogSession(tree)
    session.start()

    assert session.is_active

    session.end()

    assert not session.is_active
    assert session.current_node_id is None
