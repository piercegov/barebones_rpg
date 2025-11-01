"""Tests for the world system."""

import pytest
from barebones_rpg.world.world import World, Location, Tile
from barebones_rpg.entities.entity import Entity, Character, Enemy
from barebones_rpg.entities.stats import Stats
from barebones_rpg.core.events import EventManager, EventType


def test_get_tile_out_of_bounds():
    """Getting tiles out of bounds should return None."""
    location = Location(name="Test", width=10, height=10)

    tile = location.get_tile(-1, 5)
    assert tile is None

    tile = location.get_tile(15, 5)
    assert tile is None

    tile = location.get_tile(5, -1)
    assert tile is None

    tile = location.get_tile(5, 15)
    assert tile is None


def test_set_tile_out_of_bounds_handled_gracefully():
    """Setting tiles out of bounds should be handled gracefully."""
    location = Location(name="Test", width=10, height=10)

    tile = Tile(x=20, y=20, tile_type="wall", walkable=False)

    result = location.set_tile(20, 20, tile)

    # Out of bounds, so tile not set and returns False
    assert result is False
    assert location.get_tile(20, 20) is None


def test_entity_position_tracking():
    """Location should track entity positions."""
    location = Location(name="Test", width=10, height=10)

    entity = Entity(name="Hero", stats=Stats())
    location.add_entity(entity, 5, 5)

    assert entity.position == (5, 5)
    assert entity in location.entities


def test_location_connections_bidirectional():
    """Location connections should support bidirectional linking."""
    world = World(name="Test World")

    village = Location(name="Village", width=10, height=10)
    forest = Location(name="Forest", width=10, height=10)

    world.add_location(village)
    world.add_location(forest)

    world.connect_locations(village.id, "north", forest.id, bidirectional=True)

    assert village.get_connection("north") == forest.id
    assert forest.get_connection("south") == village.id


def test_moving_entities_between_locations():
    """Entities should be movable between locations."""
    world = World(name="Test World")

    location1 = Location(name="Location 1", width=10, height=10)
    location2 = Location(name="Location 2", width=10, height=10)

    world.add_location(location1)
    world.add_location(location2)

    world.set_current_location(location1.id)

    entity = Entity(name="Hero", stats=Stats())
    location1.add_entity(entity, 5, 5)

    world.move_entity(entity, location2.id, 3, 3)

    assert entity not in location1.entities
    assert entity in location2.entities
    assert entity.position == (3, 3)


def test_finding_entities_by_name():
    """Location should find entities by name."""
    location = Location(name="Test", width=10, height=10)

    hero = Entity(name="Hero", stats=Stats())
    goblin = Entity(name="Goblin", stats=Stats())

    location.add_entity(hero)
    location.add_entity(goblin)

    found = location.find_entity_by_name("Goblin")

    assert found is not None
    assert found.name == "Goblin"


def test_finding_entities_by_faction():
    """Location should find entities by faction."""
    location = Location(name="Test", width=10, height=10)

    hero = Character(name="Hero", stats=Stats())
    enemy1 = Enemy(name="Goblin", stats=Stats())
    enemy2 = Enemy(name="Orc", stats=Stats())

    location.add_entity(hero)
    location.add_entity(enemy1)
    location.add_entity(enemy2)

    enemies = location.find_entities_by_faction("enemy")

    assert len(enemies) == 2
    assert enemy1 in enemies
    assert enemy2 in enemies


def test_tile_walkability_checks():
    """Location should check if positions are walkable."""
    location = Location(name="Test", width=10, height=10)

    wall = Tile(x=5, y=5, tile_type="wall", walkable=False)
    result = location.set_tile(5, 5, wall)

    # Tile set successfully
    assert result is True
    assert location.is_walkable(5, 5) is False
    assert location.is_walkable(6, 6) is True


def test_world_location_switching_with_events():
    """World should publish events when switching locations."""
    events = EventManager()
    events.enable_history()

    world = World(name="Test World")

    location1 = Location(name="Location 1", width=10, height=10)
    location2 = Location(name="Location 2", width=10, height=10)

    world.add_location(location1)
    world.add_location(location2)

    world.set_current_location(location2.id, events)

    history = events.get_history()

    entered_events = [e for e in history if e.event_type == EventType.LOCATION_ENTERED]
    assert len(entered_events) >= 1


def test_world_get_current_location():
    """World should return the current location."""
    world = World(name="Test World")

    location = Location(name="Starting Area", width=10, height=10)
    world.add_location(location)

    current = world.get_current_location()

    assert current is not None
    assert current.name == "Starting Area"


def test_world_get_location_by_name():
    """World should find locations by name."""
    world = World(name="Test World")

    location = Location(name="Unique Location", width=10, height=10)
    world.add_location(location)

    found = world.get_location_by_name("Unique Location")

    assert found is not None
    assert found.id == location.id


def test_location_get_entity_at():
    """Location should find entities at specific positions."""
    location = Location(name="Test", width=10, height=10)

    entity = Entity(name="Hero", stats=Stats())
    location.add_entity(entity, 5, 5)

    found = location.get_entity_at(5, 5)

    assert found is not None
    assert found.name == "Hero"


def test_location_remove_entity():
    """Location should remove entities correctly."""
    location = Location(name="Test", width=10, height=10)

    entity = Entity(name="Hero", stats=Stats())
    location.add_entity(entity)

    assert entity in location.entities

    result = location.remove_entity(entity)

    # Entity removed successfully
    assert result is True
    assert entity not in location.entities

    # Trying to remove again should return False
    result2 = location.remove_entity(entity)
    assert result2 is False


def test_tile_can_enter():
    """Tile should check if entity can enter based on walkability."""
    walkable_tile = Tile(x=0, y=0, tile_type="grass", walkable=True)
    unwalkable_tile = Tile(x=1, y=0, tile_type="wall", walkable=False)

    entity = Entity(name="Hero", stats=Stats())

    assert walkable_tile.can_enter(entity) is True
    assert unwalkable_tile.can_enter(entity) is False


def test_location_initializes_default_tiles():
    """Location should initialize all tiles with default tile type."""
    location = Location(name="Test", width=5, height=5)

    assert len(location.tiles) == 25

    for y in range(5):
        for x in range(5):
            tile = location.get_tile(x, y)
            assert tile is not None
            assert tile.tile_type == "grass"


def test_location_on_enter_callback():
    """Location should execute on_enter callback."""
    callback_executed = {"executed": False}

    def on_enter(loc):
        callback_executed["executed"] = True

    location = Location(name="Test", width=10, height=10, on_enter=on_enter)
    world = World(name="Test World")

    world.add_location(location)
    world.set_current_location(location.id)

    assert callback_executed["executed"] is True


def test_location_on_exit_callback():
    """Location should execute on_exit callback."""
    callback_executed = {"executed": False}

    def on_exit(loc):
        callback_executed["executed"] = True

    events = EventManager()
    world = World(name="Test World")

    location1 = Location(name="Loc1", width=10, height=10, on_exit=on_exit)
    location2 = Location(name="Loc2", width=10, height=10)

    world.add_location(location1)
    world.add_location(location2)

    world.set_current_location(location1.id)
    world.set_current_location(location2.id, events)

    assert callback_executed["executed"] is True


def test_world_first_location_auto_set_as_current():
    """First location added to world should auto-set as current."""
    world = World(name="Test World")

    location = Location(name="First", width=10, height=10)
    world.add_location(location)

    assert world.current_location_id == location.id


def test_location_has_entity_named():
    """has_entity_named should check for entity existence."""
    location = Location(name="Test", width=10, height=10)

    entity = Entity(name="TestEntity", stats=Stats())
    location.add_entity(entity)

    assert location.has_entity_named("TestEntity") is True
    assert location.has_entity_named("NonExistent") is False


def test_location_find_entities_by_name():
    """find_entities_by_name should return all entities with matching name."""
    location = Location(name="Test", width=10, height=10)

    goblin1 = Enemy(name="Goblin", stats=Stats())
    goblin2 = Enemy(name="Goblin", stats=Stats())
    orc = Enemy(name="Orc", stats=Stats())

    location.add_entity(goblin1)
    location.add_entity(goblin2)
    location.add_entity(orc)

    goblins = location.find_entities_by_name("Goblin")

    assert len(goblins) == 2
    assert goblin1 in goblins
    assert goblin2 in goblins


def test_world_reverse_direction():
    """World should correctly determine reverse directions."""
    world = World(name="Test World")

    assert world._reverse_direction("north") == "south"
    assert world._reverse_direction("south") == "north"
    assert world._reverse_direction("east") == "west"
    assert world._reverse_direction("west") == "east"
    assert world._reverse_direction("up") == "down"
    assert world._reverse_direction("down") == "up"


def test_location_add_connection():
    """Location should add connections to other locations."""
    location = Location(name="Test", width=10, height=10)

    location.add_connection("north", "some_location_id")

    assert location.get_connection("north") == "some_location_id"


def test_tile_on_enter_callback():
    """Tile should support on_enter callback."""
    callback_executed = {"executed": False}

    def on_enter(entity):
        callback_executed["executed"] = True

    tile = Tile(x=0, y=0, on_enter=on_enter)
    entity = Entity(name="Hero", stats=Stats())

    if tile.on_enter:
        tile.on_enter(entity)

    assert callback_executed["executed"] is True
