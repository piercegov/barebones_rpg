"""Party system for managing groups of entities.

This module provides a persistent party system that works with combat
and can be extended for custom features like shared resources.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class Party(BaseModel):
    """A persistent party of entities.

    Parties are collections of entities that persist outside of combat.
    They provide a simple interface for managing group membership and
    can be extended for custom features like shared resources or party-wide buffs.

    Example:
        >>> from barebones_rpg.entities import Character
        >>> from barebones_rpg.party import Party
        >>>
        >>> hero = Character(name="Hero", stats=Stats(hp=100, atk=15))
        >>> mage = Character(name="Mage", stats=Stats(hp=80, atk=10))
        >>>
        >>> party = Party(name="Adventurers")
        >>> party.add_member(hero)
        >>> party.add_member(mage)
        >>> print(party.size())
        2
        >>> print(party.get_leader().name)
        Hero

    Extensibility:
        The Party class can be extended for custom behavior:

        >>> class PartyWithGold(Party):
        ...     shared_gold: int = 0
        ...
        ...     def add_gold(self, amount: int):
        ...         self.shared_gold += amount

        Or use the metadata dict for runtime customization:

        >>> party.metadata["gold"] = 100
        >>> party.metadata["formation"] = "defensive"
    """

    name: str = Field(description="Party name")
    members: List[Any] = Field(default_factory=list, description="Party members")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata for extensibility"
    )

    model_config = {"arbitrary_types_allowed": True}

    def add_member(self, member: Any) -> bool:
        """Add a member to the party.

        Args:
            member: Entity to add to the party

        Returns:
            True if member was added successfully, False if already in party
        """
        if member in self.members:
            return False
        self.members.append(member)
        return True

    def remove_member(self, member: Any) -> bool:
        """Remove a member from the party.

        Args:
            member: Entity to remove from the party

        Returns:
            True if member was found and removed, False if not in party
        """
        if member in self.members:
            self.members.remove(member)
            return True
        return False

    def get_alive_members(self) -> List[Any]:
        """Get all living members.

        Returns:
            List of alive members
        """
        return [m for m in self.members if m.is_alive()]

    def is_defeated(self) -> bool:
        """Check if entire party is defeated.

        Returns:
            True if all members are dead, False otherwise
        """
        return len(self.get_alive_members()) == 0

    def get_leader(self) -> Optional[Any]:
        """Get the party leader.

        By default, the leader is the first member in the party.
        This can be overridden in subclasses for custom leader logic.

        Returns:
            The party leader or None if party is empty
        """
        return self.members[0] if self.members else None

    def size(self) -> int:
        """Get the number of members in the party.

        Returns:
            Number of party members
        """
        return len(self.members)

    def has_member(self, member: Any) -> bool:
        """Check if an entity is in the party.

        Args:
            member: Entity to check

        Returns:
            True if member is in the party
        """
        return member in self.members

    def clear(self) -> None:
        """Remove all members from the party."""
        self.members.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert party to dictionary for saving.

        Note: This only serializes basic party structure. Entity serialization
        must be handled separately.

        Returns:
            Dictionary representation of party
        """
        return {
            "name": self.name,
            "member_ids": [m.id for m in self.members],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], entity_lookup: Dict[str, Any]) -> "Party":
        """Create party from dictionary.

        Args:
            data: Dictionary representation
            entity_lookup: Dictionary mapping entity IDs to entity objects

        Returns:
            Party instance
        """
        party = cls(name=data["name"], metadata=data.get("metadata", {}))
        for member_id in data.get("member_ids", []):
            if member_id in entity_lookup:
                party.add_member(entity_lookup[member_id])
        return party
