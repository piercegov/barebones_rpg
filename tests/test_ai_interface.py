"""Tests for AI interface."""

import pytest
from barebones_rpg.entities import (
    Entity,
    Enemy,
    AIInterface,
    AIContext,
)
from barebones_rpg.entities.stats import Stats
from barebones_rpg.world.world import Location, Tile


class SimpleTestAI(AIInterface):
    """Simple test AI that always attacks nearest entity."""

    def decide_action(self, context: AIContext) -> dict:
        if context.nearby_entities:
            target = context.nearby_entities[0]
            return {"action": "attack", "target": target}
        return {"action": "wait"}


class StateMachineAI(AIInterface):
    """Test AI using a simple state machine."""

    def __init__(self):
        self.state = "idle"

    def decide_action(self, context: AIContext) -> dict:
        entity = context.entity

        if not hasattr(entity, "stats"):
            return {"action": "wait"}

        hp_percent = entity.stats.hp / entity.stats.max_hp

        if hp_percent < 0.3:
            self.state = "flee"
        elif context.nearby_entities:
            self.state = "attack"
        else:
            self.state = "idle"

        if self.state == "flee":
            if context.nearby_entities:
                threat = context.nearby_entities[0]
                return {"action": "flee", "target": threat}

        elif self.state == "attack":
            target = context.nearby_entities[0]
            ex, ey = entity.position
            tx, ty = target.position
            distance = abs(ex - tx) + abs(ey - ty)
            if distance <= 1:
                return {"action": "attack", "target": target}
            else:
                return {"action": "move", "position": target.position}

        return {"action": "wait"}


@pytest.fixture
def test_entity():
    """Create a test entity."""
    return Entity(
        name="Test Entity",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=10,
            dexterity=10,
            charisma=10,
            base_max_hp=100,
            hp=100,
        ),
        position=(0, 0),
    )


@pytest.fixture
def test_enemy():
    """Create a test enemy."""
    return Enemy(
        name="Test Enemy",
        stats=Stats(
            strength=8,
            constitution=8,
            intelligence=5,
            dexterity=10,
            charisma=5,
            base_max_hp=50,
            hp=50,
        ),
        position=(5, 5),
    )


@pytest.fixture
def test_location():
    """Create a test location."""
    loc = Location(name="Test", description="Test location", width=10, height=10)
    for y in range(10):
        for x in range(10):
            loc.set_tile(x, y, Tile(x=x, y=y, tile_type="floor", walkable=True))
    return loc


class TestAIContext:
    """Tests for AIContext."""

    def test_create_basic_context(self, test_entity):
        """Test creating a basic context."""
        context = AIContext(entity=test_entity, nearby_entities=[])
        assert context.entity == test_entity
        assert context.nearby_entities == []

    def test_create_context_with_nearby_entities(self, test_entity, test_enemy):
        """Test creating context with nearby entities."""
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        assert context.entity == test_entity
        assert len(context.nearby_entities) == 1
        assert context.nearby_entities[0] == test_enemy

    def test_context_metadata(self, test_entity):
        """Test context metadata."""
        context = AIContext(entity=test_entity, metadata={"custom_key": "custom_value"})
        assert context.metadata["custom_key"] == "custom_value"


class TestAIInterface:
    """Tests for AIInterface implementations."""

    def test_simple_test_ai_attack(self, test_entity, test_enemy):
        """Test SimpleTestAI attacking."""
        ai = SimpleTestAI()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = ai.decide_action(context)
        assert action["action"] == "attack"
        assert action["target"] == test_enemy

    def test_simple_test_ai_wait(self, test_entity):
        """Test SimpleTestAI waiting when no targets."""
        ai = SimpleTestAI()
        context = AIContext(entity=test_entity, nearby_entities=[])
        action = ai.decide_action(context)
        assert action["action"] == "wait"

    def test_state_machine_ai_attack(self, test_entity, test_enemy):
        """Test StateMachineAI in attack state."""
        test_entity.position = (5, 5)
        test_enemy.position = (5, 6)  # Adjacent
        ai = StateMachineAI()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = ai.decide_action(context)
        assert action["action"] == "attack"
        assert ai.state == "attack"

    def test_state_machine_ai_flee(self, test_entity, test_enemy):
        """Test StateMachineAI fleeing when low HP."""
        test_entity.stats.hp = 10  # Low HP
        ai = StateMachineAI()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = ai.decide_action(context)
        assert action["action"] == "flee"
        assert ai.state == "flee"

    def test_state_machine_ai_idle(self, test_entity):
        """Test StateMachineAI in idle state."""
        ai = StateMachineAI()
        context = AIContext(entity=test_entity, nearby_entities=[])
        action = ai.decide_action(context)
        assert action["action"] == "wait"
        assert ai.state == "idle"


class TestEntityAI:
    """Tests for entity ai field."""

    def test_entity_default_ai(self):
        """Test entity default ai is None."""
        entity = Entity(name="Test")
        assert entity.ai is None

    def test_entity_set_ai(self):
        """Test setting entity ai."""
        entity = Entity(name="Test")
        ai = SimpleTestAI()
        entity.ai = ai
        assert entity.ai is ai

    def test_enemy_with_ai(self):
        """Test creating enemy with AI."""
        ai = SimpleTestAI()
        enemy = Enemy(
            name="Enemy",
            ai=ai,
            stats=Stats(
                strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
            ),
        )
        assert enemy.ai is ai
