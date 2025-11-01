"""Tests for the event system."""

import pytest
from barebones_rpg.core.events import EventManager, Event, EventType


def test_publish_with_no_subscribers(event_manager):
    """Publishing an event with no subscribers should not error."""
    event = Event(EventType.DAMAGE_DEALT, {"amount": 10})
    event_manager.publish(event)


def test_unsubscribe_never_subscribed(event_manager):
    """Unsubscribing a callback that was never subscribed should fail gracefully."""

    def callback(event):
        pass

    try:
        event_manager.unsubscribe(EventType.DAMAGE_DEALT, callback)
    except ValueError:
        pass


def test_multiple_subscribers_same_event(event_manager):
    """Multiple subscribers should all receive the same event."""
    call_counts = {"sub1": 0, "sub2": 0, "sub3": 0}

    def subscriber1(event):
        call_counts["sub1"] += 1

    def subscriber2(event):
        call_counts["sub2"] += 1

    def subscriber3(event):
        call_counts["sub3"] += 1

    event_manager.subscribe(EventType.DAMAGE_DEALT, subscriber1)
    event_manager.subscribe(EventType.DAMAGE_DEALT, subscriber2)
    event_manager.subscribe(EventType.DAMAGE_DEALT, subscriber3)

    event = Event(EventType.DAMAGE_DEALT, {"amount": 15})
    event_manager.publish(event)

    assert call_counts["sub1"] == 1
    assert call_counts["sub2"] == 1
    assert call_counts["sub3"] == 1


def test_event_history_recording(event_manager):
    """Event history should record when enabled and not record when disabled."""
    event_manager.enable_history()

    event1 = Event(EventType.COMBAT_START, {})
    event2 = Event(EventType.DAMAGE_DEALT, {"amount": 10})

    event_manager.publish(event1)
    event_manager.publish(event2)

    history = event_manager.get_history()
    assert len(history) == 2
    assert history[0].event_type == EventType.COMBAT_START
    assert history[1].event_type == EventType.DAMAGE_DEALT

    event_manager.disable_history()
    event3 = Event(EventType.COMBAT_END, {})
    event_manager.publish(event3)

    history = event_manager.get_history()
    assert len(history) == 2


def test_clear_history(event_manager):
    """Clear history should empty the event history."""
    event_manager.enable_history()

    for i in range(5):
        event_manager.publish(Event(EventType.DAMAGE_DEALT, {"amount": i}))

    assert len(event_manager.get_history()) == 5

    event_manager.clear_history()
    assert len(event_manager.get_history()) == 0


def test_custom_string_event_types(event_manager):
    """Event system should support custom string event types, not just EventType enum."""
    received_events = []

    def custom_handler(event):
        received_events.append(event)

    event_manager.subscribe("custom_event_type", custom_handler)

    custom_event = Event("custom_event_type", {"data": "test"})
    event_manager.publish(custom_event)

    assert len(received_events) == 1
    assert received_events[0].event_type == "custom_event_type"
    assert received_events[0].data["data"] == "test"


def test_event_data_defaults_to_empty_dict():
    """Event data should default to an empty dict if not provided."""
    event = Event(EventType.GAME_START)
    assert event.data == {}


def test_subscribe_and_unsubscribe_workflow(event_manager):
    """Test subscribing, publishing, unsubscribing, and verifying callback not called."""
    call_count = {"count": 0}

    def callback(event):
        call_count["count"] += 1

    event_manager.subscribe(EventType.LEVEL_UP, callback)
    event_manager.publish(Event(EventType.LEVEL_UP, {}))
    assert call_count["count"] == 1

    event_manager.unsubscribe(EventType.LEVEL_UP, callback)
    event_manager.publish(Event(EventType.LEVEL_UP, {}))
    assert call_count["count"] == 1


def test_clear_all_subscribers(event_manager):
    """Clear all subscribers should remove all subscriptions."""

    def callback1(event):
        pass

    def callback2(event):
        pass

    event_manager.subscribe(EventType.DAMAGE_DEALT, callback1)
    event_manager.subscribe(EventType.HEAL, callback2)

    event_manager.clear_all_subscribers()

    assert len(event_manager._subscribers) == 0
