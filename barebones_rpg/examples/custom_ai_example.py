"""Custom AI implementation examples.

This example demonstrates how to implement custom AI for entities using
the AIInterface. It shows two approaches:
1. State Machine AI - using discrete states for behavior
2. Mock LLM AI - simulating LLM-based decision making

These examples show the flexibility of the AI system and how users can
implement any AI approach they want (behavior trees, utility AI, actual LLMs, etc.)
"""

from enum import Enum
from typing import Optional
import random

from barebones_rpg.entities import (
    Entity,
    Enemy,
    Character,
    AIInterface,
    AIContext,
    Stats,
)


# Example 1: State Machine AI


class AIState(Enum):
    """States for state machine AI."""

    IDLE = "idle"
    PATROL = "patrol"
    CHASE = "chase"
    ATTACK = "attack"
    FLEE = "flee"
    GUARD = "guard"


class StateMachineAI(AIInterface):
    """AI using a finite state machine.

    This AI tracks state and transitions between behaviors based on
    conditions like health, distance to target, and perception.

    Example usage:
        >>> ai = StateMachineAI(patrol_points=[(5, 5), (10, 10)])
        >>> guard = Enemy(name="Guard", ai=ai)
    """

    def __init__(
        self,
        patrol_points: Optional[list[tuple[int, int]]] = None,
        guard_position: Optional[tuple[int, int]] = None,
        flee_threshold: float = 0.25,
        chase_range: int = 5,
    ):
        """Initialize the state machine AI.

        Args:
            patrol_points: Points to patrol between
            guard_position: Position to guard (if set, ignores patrol)
            flee_threshold: HP percentage to start fleeing
            chase_range: Distance at which to chase enemies
        """
        self.state = AIState.IDLE
        self.patrol_points = patrol_points or []
        self.current_patrol_index = 0
        self.guard_position = guard_position
        self.flee_threshold = flee_threshold
        self.chase_range = chase_range

    def decide_action(self, context: AIContext) -> dict:
        """Decide action based on current state and context."""
        entity = context.entity

        # Evaluate conditions and transition states
        self._update_state(context)

        # Execute state behavior
        if self.state == AIState.IDLE:
            return {"action": "wait"}

        elif self.state == AIState.PATROL:
            return self._patrol_behavior(context)

        elif self.state == AIState.GUARD:
            return self._guard_behavior(context)

        elif self.state == AIState.CHASE:
            return self._chase_behavior(context)

        elif self.state == AIState.ATTACK:
            return self._attack_behavior(context)

        elif self.state == AIState.FLEE:
            return self._flee_behavior(context)

        return {"action": "wait"}

    def _update_state(self, context: AIContext):
        """Update state based on conditions."""
        entity = context.entity

        # Check health for flee condition
        if hasattr(entity, "stats"):
            hp_percent = entity.stats.hp / entity.stats.max_hp
            if hp_percent < self.flee_threshold:
                self.state = AIState.FLEE
                return

        # Check for nearby enemies
        if context.nearby_entities:
            target = context.nearby_entities[0]
            distance = self._distance(entity.position, target.position)

            if distance <= 1:
                self.state = AIState.ATTACK
            elif distance <= self.chase_range:
                self.state = AIState.CHASE
            elif self.guard_position:
                self.state = AIState.GUARD
            elif self.patrol_points:
                self.state = AIState.PATROL
            else:
                self.state = AIState.IDLE
        else:
            # No enemies nearby
            if self.guard_position:
                self.state = AIState.GUARD
            elif self.patrol_points:
                self.state = AIState.PATROL
            else:
                self.state = AIState.IDLE

    def _patrol_behavior(self, context: AIContext) -> dict:
        """Patrol between waypoints."""
        if not self.patrol_points:
            return {"action": "wait"}

        target_point = self.patrol_points[self.current_patrol_index]

        if context.entity.position == target_point:
            # Reached waypoint, move to next
            self.current_patrol_index = (self.current_patrol_index + 1) % len(
                self.patrol_points
            )
            target_point = self.patrol_points[self.current_patrol_index]

        return {"action": "move", "position": target_point}

    def _guard_behavior(self, context: AIContext) -> dict:
        """Return to guard position."""
        if context.entity.position == self.guard_position:
            return {"action": "wait"}
        return {"action": "move", "position": self.guard_position}

    def _chase_behavior(self, context: AIContext) -> dict:
        """Chase the nearest enemy."""
        if not context.nearby_entities:
            return {"action": "wait"}

        target = context.nearby_entities[0]
        return {"action": "move", "position": target.position}

    def _attack_behavior(self, context: AIContext) -> dict:
        """Attack the nearest enemy."""
        if not context.nearby_entities:
            return {"action": "wait"}

        target = context.nearby_entities[0]
        return {"action": "attack", "target": target}

    def _flee_behavior(self, context: AIContext) -> dict:
        """Flee from nearest threat."""
        if not context.nearby_entities:
            return {"action": "wait"}

        threat = context.nearby_entities[0]
        return {"action": "flee", "target": threat, "run_speed": 2}

    def _distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        """Calculate Manhattan distance."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


# Example 2: Mock LLM AI


class MockLLMAI(AIInterface):
    """Mock LLM-based AI that simulates decision making.

    This demonstrates how you could integrate an actual LLM (like GPT, Claude, etc.)
    into the AI system. In real usage, you'd call an actual LLM API here.

    Example usage:
        >>> ai = MockLLMAI(personality="aggressive warrior")
        >>> boss = Enemy(name="Boss", ai=ai)
    """

    def __init__(self, personality: str = "neutral", temperature: float = 0.7):
        """Initialize mock LLM AI.

        Args:
            personality: Personality description for the AI
            temperature: Randomness in decisions (0.0-1.0)
        """
        self.personality = personality
        self.temperature = temperature
        self.decision_history: list[str] = []

    def decide_action(self, context: AIContext) -> dict:
        """Decide action using mock LLM reasoning."""
        # In real implementation, you'd call an LLM API here with a prompt like:
        #
        # prompt = f"""
        # You are a {self.personality} in an RPG game.
        # Current HP: {context.entity.stats.hp}/{context.entity.stats.max_hp}
        # Position: {context.entity.position}
        # Nearby enemies: {len(context.nearby_entities)}
        # Recent actions: {self.decision_history[-3:]}
        #
        # What action should you take? Choose from:
        # - attack: Attack nearest enemy
        # - move: Move to a position
        # - wait: Do nothing
        # - flee: Run away
        # - use_skill: Use a special ability
        # """
        #
        # response = call_llm(prompt)
        # return self._parse_llm_response(response)

        # Mock implementation - simulate LLM decision making
        decision = self._mock_llm_decision(context)
        self.decision_history.append(decision)

        if len(self.decision_history) > 10:
            self.decision_history.pop(0)

        return self._parse_decision(decision, context)

    def _mock_llm_decision(self, context: AIContext) -> str:
        """Simulate an LLM's decision-making process."""
        entity = context.entity

        # Simulate reasoning based on personality and context
        if hasattr(entity, "stats"):
            hp_percent = entity.stats.hp / entity.stats.max_hp

            if hp_percent < 0.3:
                return "flee" if random.random() < 0.7 else "attack"

            if context.nearby_entities:
                distance = abs(
                    entity.position[0] - context.nearby_entities[0].position[0]
                ) + abs(entity.position[1] - context.nearby_entities[0].position[1])

                if distance <= 1:
                    # "Aggressive" personalities attack more
                    if "aggressive" in self.personality.lower():
                        return "attack"
                    # "Defensive" personalities might use skills
                    elif "defensive" in self.personality.lower():
                        return "use_skill" if random.random() < 0.3 else "attack"
                    else:
                        return "attack" if random.random() < 0.8 else "wait"
                else:
                    return "move"

        return "wait"

    def _parse_decision(self, decision: str, context: AIContext) -> dict:
        """Parse the mock LLM decision into an action dict."""
        if decision == "attack" and context.nearby_entities:
            return {
                "action": "attack",
                "target": context.nearby_entities[0],
                "reasoning": f"As a {self.personality}, I choose to attack",
            }

        elif decision == "move" and context.nearby_entities:
            target = context.nearby_entities[0]
            return {
                "action": "move",
                "position": target.position,
                "reasoning": f"Moving toward target as a {self.personality}",
            }

        elif decision == "flee" and context.nearby_entities:
            return {
                "action": "flee",
                "target": context.nearby_entities[0],
                "reasoning": "Low health, retreating to survive",
            }

        elif decision == "use_skill":
            return {
                "action": "use_skill",
                "skill_name": "defensive_stance",
                "reasoning": "Using skill to improve survivability",
            }

        return {
            "action": "wait",
            "reasoning": "Observing the situation",
        }


def main():
    """Demonstrate custom AI implementations."""
    print("=== Custom AI Example ===\n")

    # Create AI instances
    patrol_ai = StateMachineAI(patrol_points=[(5, 5), (10, 5), (10, 10), (5, 10)])
    guard_ai = StateMachineAI(guard_position=(15, 15))
    aggressive_ai = MockLLMAI(personality="aggressive warrior")

    # Create test entities
    player = Character(
        name="Hero",
        stats=Stats(
            strength=15,
            constitution=12,
            intelligence=10,
            dexterity=14,
            charisma=10,
            base_max_hp=100,
            hp=100,
        ),
        position=(8, 8),
    )

    patrol_guard = Enemy(
        name="Patrol Guard",
        stats=Stats(
            strength=10,
            constitution=10,
            intelligence=8,
            dexterity=10,
            charisma=5,
            base_max_hp=50,
            hp=50,
        ),
        position=(5, 5),
        ai=patrol_ai,
    )

    static_guard = Enemy(
        name="Static Guard",
        stats=Stats(
            strength=12,
            constitution=12,
            intelligence=6,
            dexterity=8,
            charisma=5,
            base_max_hp=60,
            hp=60,
        ),
        position=(14, 14),
        ai=guard_ai,
    )

    aggressive_boss = Enemy(
        name="Aggressive Boss",
        stats=Stats(
            strength=20,
            constitution=18,
            intelligence=12,
            dexterity=15,
            charisma=10,
            base_max_hp=150,
            hp=150,
        ),
        position=(20, 20),
        ai=aggressive_ai,
    )

    # Simulate a few turns
    print("Simulating AI decisions...\n")

    enemies = [patrol_guard, static_guard, aggressive_boss]

    for turn in range(3):
        print(f"--- Turn {turn + 1} ---")

        for enemy in enemies:
            # Build context
            context = AIContext(entity=enemy, nearby_entities=[player])

            # Call AI directly
            if enemy.ai:
                action = enemy.ai.decide_action(context)

                if action:
                    print(f"{enemy.name}:")
                    print(f"  Action: {action.get('action', 'unknown')}")
                    if action.get("target"):
                        print(f"  Target: {action['target'].name}")
                    if action.get("position"):
                        print(f"  Position: {action['position']}")
                    if action.get("reasoning"):
                        print(f"  Reasoning: {action['reasoning']}")
            print()

        print()

    print("\n=== Example Complete ===")
    print("\nKey takeaways:")
    print("1. AIInterface allows any AI implementation approach")
    print("2. State machines provide predictable, deterministic behavior")
    print("3. LLM-based AI can provide dynamic, contextual decisions")
    print("4. Users assign AI instances directly to entities")
    print("5. AI decisions are simple dicts that users can easily parse")


if __name__ == "__main__":
    main()
