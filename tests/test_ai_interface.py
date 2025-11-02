"""Tests for AI interface, registry, and system."""

import pytest
from barebones_rpg.entities import (
    Entity,
    Enemy,
    AIInterface,
    AIContext,
    AIAction,
    AIRegistry,
    AISystem,
)
from barebones_rpg.entities.stats import Stats
from barebones_rpg.world.world import Location, Tile


class SimpleTestAI(AIInterface):
    """Simple test AI that always attacks nearest entity."""

    def decide_action(self, context: AIContext):
        if context.nearby_entities:
            target = context.nearby_entities[0]
            return AIAction(action_type="attack", target=target)
        return AIAction(action_type="wait")


class StateMachineAI(AIInterface):
    """Test AI using a simple state machine."""

    def __init__(self):
        self.state = "idle"

    def decide_action(self, context: AIContext):
        entity = context.entity

        if not hasattr(entity, "stats"):
            return AIAction(action_type="wait")

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
                return AIAction(action_type="flee", target=threat)
        elif self.state == "attack":
            target = context.nearby_entities[0]
            ex, ey = entity.position
            tx, ty = target.position
            distance = abs(ex - tx) + abs(ey - ty)
            if distance <= 1:
                return AIAction(action_type="attack", target=target)
            else:
                return AIAction(action_type="move", target_position=target.position)

        return AIAction(action_type="wait")


@pytest.fixture
def clear_registry():
    """Clear AI registry before each test."""
    AIRegistry.clear()
    yield
    AIRegistry.clear()


@pytest.fixture
def test_entity():
    """Create a test entity."""
    stats = Stats(
        strength=10,
        constitution=10,
        intelligence=10,
        dexterity=10,
        charisma=10,
        base_max_hp=100,
        hp=100,
    )
    entity = Entity(name="Test Entity", stats=stats, position=(5, 5))
    return entity


@pytest.fixture
def test_enemy():
    """Create a test enemy."""
    stats = Stats(
        strength=8,
        constitution=8,
        intelligence=8,
        dexterity=8,
        charisma=8,
        base_max_hp=50,
        hp=50,
    )
    enemy = Enemy(name="Test Enemy", stats=stats, position=(3, 3))
    return enemy


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
        """Test creating a basic AI context."""
        context = AIContext(entity=test_entity)
        assert context.entity == test_entity
        assert context.world is None
        assert context.location is None
        assert len(context.nearby_entities) == 0

    def test_create_context_with_nearby_entities(self, test_entity, test_enemy):
        """Test creating context with nearby entities."""
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        assert len(context.nearby_entities) == 1
        assert context.nearby_entities[0] == test_enemy

    def test_context_metadata(self, test_entity):
        """Test context metadata."""
        context = AIContext(entity=test_entity, metadata={"custom_key": "custom_value"})
        assert context.metadata["custom_key"] == "custom_value"


class TestAIAction:
    """Tests for AIAction."""

    def test_create_attack_action(self, test_enemy):
        """Test creating an attack action."""
        action = AIAction(action_type="attack", target=test_enemy)
        assert action.action_type == "attack"
        assert action.target == test_enemy
        assert action.target_position is None

    def test_create_move_action(self):
        """Test creating a move action."""
        action = AIAction(action_type="move", target_position=(10, 5))
        assert action.action_type == "move"
        assert action.target_position == (10, 5)
        assert action.target is None

    def test_create_wait_action(self):
        """Test creating a wait action."""
        action = AIAction(action_type="wait")
        assert action.action_type == "wait"

    def test_action_parameters(self):
        """Test action with custom parameters."""
        action = AIAction(
            action_type="use_skill", parameters={"skill_name": "fireball", "power": 50}
        )
        assert action.parameters["skill_name"] == "fireball"
        assert action.parameters["power"] == 50


class TestAIInterface:
    """Tests for AIInterface implementations."""

    def test_simple_test_ai_attack(self, test_entity, test_enemy):
        """Test SimpleTestAI attacking."""
        ai = SimpleTestAI()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = ai.decide_action(context)
        assert action.action_type == "attack"
        assert action.target == test_enemy

    def test_simple_test_ai_wait(self, test_entity):
        """Test SimpleTestAI waiting when no targets."""
        ai = SimpleTestAI()
        context = AIContext(entity=test_entity, nearby_entities=[])
        action = ai.decide_action(context)
        assert action.action_type == "wait"

    def test_state_machine_ai_attack(self, test_entity, test_enemy):
        """Test StateMachineAI in attack state."""
        ai = StateMachineAI()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = ai.decide_action(context)
        assert action.action_type in ["attack", "move"]
        assert ai.state == "attack"

    def test_state_machine_ai_flee(self, test_enemy):
        """Test StateMachineAI in flee state."""
        test_enemy.stats.hp = 10
        ai = StateMachineAI()
        player = Entity(
            name="Player",
            stats=Stats(
                strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
            ),
            position=(4, 4),
        )
        context = AIContext(entity=test_enemy, nearby_entities=[player])
        action = ai.decide_action(context)
        assert action.action_type == "flee"
        assert ai.state == "flee"

    def test_state_machine_ai_idle(self, test_entity):
        """Test StateMachineAI in idle state."""
        ai = StateMachineAI()
        context = AIContext(entity=test_entity, nearby_entities=[])
        action = ai.decide_action(context)
        assert action.action_type == "wait"
        assert ai.state == "idle"


class TestAIRegistry:
    """Tests for AIRegistry."""

    def test_register_ai(self, clear_registry):
        """Test registering AI."""
        ai = SimpleTestAI()
        AIRegistry.register("simple_test", ai)
        assert AIRegistry.has("simple_test")

    def test_get_ai(self, clear_registry):
        """Test getting registered AI."""
        ai = SimpleTestAI()
        AIRegistry.register("simple_test", ai)
        retrieved = AIRegistry.get("simple_test")
        assert retrieved is ai

    def test_get_nonexistent_ai(self, clear_registry):
        """Test getting non-existent AI returns None."""
        retrieved = AIRegistry.get("nonexistent")
        assert retrieved is None

    def test_has_ai(self, clear_registry):
        """Test checking if AI exists."""
        ai = SimpleTestAI()
        AIRegistry.register("test", ai)
        assert AIRegistry.has("test")
        assert not AIRegistry.has("nonexistent")

    def test_get_all_names(self, clear_registry):
        """Test getting all registered AI names."""
        AIRegistry.register("ai1", SimpleTestAI())
        AIRegistry.register("ai2", StateMachineAI())
        names = AIRegistry.get_all_names()
        assert "ai1" in names
        assert "ai2" in names
        assert len(names) == 2

    def test_clear_registry(self, clear_registry):
        """Test clearing the registry."""
        AIRegistry.register("test", SimpleTestAI())
        assert AIRegistry.has("test")
        AIRegistry.clear()
        assert not AIRegistry.has("test")


class TestAISystem:
    """Tests for AISystem."""

    def test_create_ai_system(self):
        """Test creating an AI system."""
        system = AISystem()
        assert system.registry == AIRegistry

    def test_get_ai(self, clear_registry):
        """Test getting AI through system."""
        ai = SimpleTestAI()
        AIRegistry.register("test", ai)
        system = AISystem()
        retrieved = system.get_ai("test")
        assert retrieved is ai

    def test_process_entity_with_ai(self, clear_registry, test_entity, test_enemy):
        """Test processing entity with AI."""
        test_entity.ai_type = "simple_test"
        ai = SimpleTestAI()
        AIRegistry.register("simple_test", ai)

        system = AISystem()
        context = AIContext(entity=test_entity, nearby_entities=[test_enemy])
        action = system.process_entity(test_entity, context)

        assert action is not None
        assert action.action_type == "attack"
        assert action.target == test_enemy

    def test_process_entity_without_ai(self, test_entity):
        """Test processing entity without AI returns None."""
        system = AISystem()
        context = AIContext(entity=test_entity)
        action = system.process_entity(test_entity, context)
        assert action is None

    def test_process_entity_with_unregistered_ai(self, test_entity):
        """Test processing entity with unregistered AI."""
        test_entity.ai_type = "nonexistent"
        system = AISystem()
        context = AIContext(entity=test_entity)
        action = system.process_entity(test_entity, context)
        assert action is None

    def test_process_entities(self, clear_registry, test_entity, test_enemy):
        """Test processing multiple entities."""
        entity1 = Enemy(
            name="Enemy1",
            stats=Stats(
                strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
            ),
            position=(2, 2),
            ai_type="simple_test",
        )
        entity2 = Enemy(
            name="Enemy2",
            stats=Stats(
                strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
            ),
            position=(8, 8),
            ai_type="simple_test",
        )

        AIRegistry.register("simple_test", SimpleTestAI())
        system = AISystem()

        def make_context(entity):
            return AIContext(entity=entity, nearby_entities=[test_entity])

        results = system.process_entities([entity1, entity2], make_context)

        assert len(results) == 2
        assert results[0][0] == entity1
        assert results[0][1].action_type == "attack"
        assert results[1][0] == entity2
        assert results[1][1].action_type == "attack"

    def test_process_entities_with_callback(self, clear_registry, test_entity):
        """Test processing entities with callback."""
        entity1 = Enemy(
            name="Enemy1",
            stats=Stats(
                strength=10, constitution=10, intelligence=10, dexterity=10, charisma=10
            ),
            position=(2, 2),
            ai_type="simple_test",
        )

        AIRegistry.register("simple_test", SimpleTestAI())
        system = AISystem()

        actions_executed = []

        def make_context(entity):
            return AIContext(entity=entity, nearby_entities=[test_entity])

        def execute_action(entity, action):
            actions_executed.append((entity, action))

        count = system.process_entities_with_callback(
            [entity1], make_context, execute_action
        )

        assert count == 1
        assert len(actions_executed) == 1
        assert actions_executed[0][0] == entity1
        assert actions_executed[0][1].action_type == "attack"

    def test_has_ai(self, clear_registry, test_entity):
        """Test checking if entity has AI."""
        system = AISystem()

        test_entity.ai_type = None
        assert not system.has_ai(test_entity)

        test_entity.ai_type = "simple_test"
        assert not system.has_ai(test_entity)

        AIRegistry.register("simple_test", SimpleTestAI())
        assert system.has_ai(test_entity)


class TestEntityAIType:
    """Tests for entity ai_type field."""

    def test_entity_default_ai_type(self):
        """Test entity default ai_type is None."""
        entity = Entity(name="Test")
        assert entity.ai_type is None

    def test_entity_with_ai_type(self):
        """Test creating entity with ai_type."""
        entity = Enemy(name="Goblin", ai_type="aggressive")
        assert entity.ai_type == "aggressive"

    def test_change_ai_type(self):
        """Test changing entity's ai_type."""
        entity = Enemy(name="Goblin", ai_type="aggressive")
        entity.ai_type = "defensive"
        assert entity.ai_type == "defensive"
