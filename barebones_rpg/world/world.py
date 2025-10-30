"""World and map system.

This module provides the world/map system for managing locations,
areas, and navigation.
"""

from typing import Optional, List, Dict, Any, Callable, Set, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field

from ..core.events import EventManager, Event, EventType


class Tile(BaseModel):
    """A single tile in a map.

    Tiles can have different properties like walkability, events, etc.
    """

    x: int = Field(description="X coordinate")
    y: int = Field(description="Y coordinate")
    tile_type: str = Field(default="grass", description="Type of tile (grass, wall, water, etc.)")
    walkable: bool = Field(default=True, description="Can be walked on")
    sprite_id: Optional[str] = Field(default=None, description="Sprite/texture ID for rendering")
    on_enter: Optional[Callable] = Field(
        default=None, description="Function called when entity enters tile"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def can_enter(self, entity: Any) -> bool:
        """Check if an entity can enter this tile.

        Args:
            entity: Entity attempting to enter

        Returns:
            True if tile can be entered
        """
        return self.walkable


class Location(BaseModel):
    """A location in the world (town, dungeon, area, etc.).

    Locations contain a grid of tiles and can have entities.

    Example:
        >>> location = Location(
        ...     name="Village Square",
        ...     width=20,
        ...     height=20
        ... )
        >>> # Add some walls
        >>> for x in range(20):
        ...     location.set_tile(x, 0, Tile(x=x, y=0, tile_type="wall", walkable=False))
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique location ID")
    name: str = Field(description="Location name")
    description: str = Field(default="", description="Location description")

    # Map dimensions
    width: int = Field(default=20, description="Map width")
    height: int = Field(default=20, description="Map height")

    # Tiles
    tiles: Dict[Tuple[int, int], Tile] = Field(
        default_factory=dict, description="Map tiles indexed by (x, y)"
    )
    default_tile_type: str = Field(default="grass", description="Default tile type")

    # Entities in this location
    entities: List[Any] = Field(default_factory=list, description="Entities in location")

    # Connections to other locations
    connections: Dict[str, str] = Field(
        default_factory=dict, description="Connections to other locations (direction -> location_id)"
    )

    # Events
    on_enter: Optional[Callable] = Field(
        default=None, description="Function called when location is entered"
    )
    on_exit: Optional[Callable] = Field(
        default=None, description="Function called when location is exited"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize default tiles if none exist
        if not self.tiles:
            self._initialize_tiles()

    def _initialize_tiles(self) -> None:
        """Initialize all tiles with default tile type."""
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[(x, y)] = Tile(
                    x=x, y=y, tile_type=self.default_tile_type, walkable=True
                )

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get a tile at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tile or None if out of bounds
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles.get((x, y))
        return None

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """Set a tile at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            tile: Tile to set
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[(x, y)] = tile

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if position can be walked on
        """
        tile = self.get_tile(x, y)
        return tile is not None and tile.walkable

    def get_entity_at(self, x: int, y: int) -> Optional[Any]:
        """Get an entity at a position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Entity at position or None
        """
        for entity in self.entities:
            if hasattr(entity, "position") and entity.position == (x, y):
                return entity
        return None

    def add_entity(self, entity: Any, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Add an entity to the location.

        Args:
            entity: Entity to add
            x: X coordinate (uses entity's position if None)
            y: Y coordinate (uses entity's position if None)
        """
        if x is not None and y is not None:
            entity.position = (x, y)

        if entity not in self.entities:
            self.entities.append(entity)

    def remove_entity(self, entity: Any) -> None:
        """Remove an entity from the location.

        Args:
            entity: Entity to remove
        """
        if entity in self.entities:
            self.entities.remove(entity)
    
    def find_entity_by_name(self, name: str) -> Optional[Any]:
        """Find an entity by name.
        
        Args:
            name: Entity name to search for
            
        Returns:
            First entity with matching name or None
        """
        for entity in self.entities:
            if hasattr(entity, 'name') and entity.name == name:
                return entity
        return None
    
    def find_entities_by_name(self, name: str) -> List[Any]:
        """Find all entities with a given name.
        
        Args:
            name: Entity name to search for
            
        Returns:
            List of entities with matching name
        """
        return [e for e in self.entities if hasattr(e, 'name') and e.name == name]
    
    def find_entities_by_faction(self, faction: str) -> List[Any]:
        """Find all entities of a given faction.
        
        Args:
            faction: Faction to search for (e.g., "enemy", "player", "neutral")
            
        Returns:
            List of entities with matching faction
        """
        return [e for e in self.entities if hasattr(e, 'faction') and e.faction == faction]
    
    def has_entity_named(self, name: str) -> bool:
        """Check if an entity with the given name exists in this location.
        
        Args:
            name: Entity name to check for
            
        Returns:
            True if entity exists
        """
        return self.find_entity_by_name(name) is not None

    def add_connection(self, direction: str, location_id: str) -> None:
        """Add a connection to another location.

        Args:
            direction: Direction name (north, south, east, west, etc.)
            location_id: ID of connected location
        """
        self.connections[direction] = location_id

    def get_connection(self, direction: str) -> Optional[str]:
        """Get connected location ID for a direction.

        Args:
            direction: Direction name

        Returns:
            Location ID or None
        """
        return self.connections.get(direction)


class World(BaseModel):
    """The game world containing all locations.

    Example:
        >>> world = World(name="Fantasy World")
        >>> village = Location(name="Starting Village", width=30, height=30)
        >>> forest = Location(name="Dark Forest", width=40, height=40)
        >>> world.add_location(village)
        >>> world.add_location(forest)
        >>> world.connect_locations(village.id, "north", forest.id)
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique world ID")
    name: str = Field(description="World name")
    description: str = Field(default="", description="World description")

    locations: Dict[str, Location] = Field(
        default_factory=dict, description="All locations in the world"
    )
    current_location_id: Optional[str] = Field(
        default=None, description="Current active location"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom data")

    model_config = {"arbitrary_types_allowed": True}

    def add_location(self, location: Location) -> None:
        """Add a location to the world.

        Args:
            location: Location to add
        """
        self.locations[location.id] = location

        # Set as current location if none set
        if self.current_location_id is None:
            self.current_location_id = location.id

    def get_location(self, location_id: str) -> Optional[Location]:
        """Get a location by ID.

        Args:
            location_id: Location ID

        Returns:
            Location or None
        """
        return self.locations.get(location_id)

    def get_location_by_name(self, name: str) -> Optional[Location]:
        """Get a location by name.

        Args:
            name: Location name

        Returns:
            Location or None
        """
        for location in self.locations.values():
            if location.name == name:
                return location
        return None

    def get_current_location(self) -> Optional[Location]:
        """Get the current active location.

        Returns:
            Current location or None
        """
        if self.current_location_id:
            return self.locations.get(self.current_location_id)
        return None

    def set_current_location(self, location_id: str, events: Optional[EventManager] = None) -> bool:
        """Set the current location.

        Args:
            location_id: ID of location to make current
            events: Event manager for publishing events

        Returns:
            True if location was changed
        """
        if location_id not in self.locations:
            return False

        old_location = self.get_current_location()
        if old_location and old_location.on_exit:
            old_location.on_exit(old_location)

        if events and old_location:
            events.publish(Event(EventType.LOCATION_EXITED, {"location": old_location}))

        self.current_location_id = location_id

        new_location = self.get_current_location()
        if new_location and new_location.on_enter:
            new_location.on_enter(new_location)

        if events and new_location:
            events.publish(Event(EventType.LOCATION_ENTERED, {"location": new_location}))

        return True

    def connect_locations(
        self,
        from_location_id: str,
        direction: str,
        to_location_id: str,
        bidirectional: bool = False
    ) -> None:
        """Connect two locations.

        Args:
            from_location_id: Starting location ID
            direction: Direction of connection
            to_location_id: Destination location ID
            bidirectional: If True, create reverse connection too
        """
        from_location = self.get_location(from_location_id)
        if from_location:
            from_location.add_connection(direction, to_location_id)

        if bidirectional:
            # Create reverse direction
            reverse_dir = self._reverse_direction(direction)
            to_location = self.get_location(to_location_id)
            if to_location:
                to_location.add_connection(reverse_dir, from_location_id)

    def _reverse_direction(self, direction: str) -> str:
        """Get the reverse of a direction.

        Args:
            direction: Direction name

        Returns:
            Reverse direction
        """
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
            "up": "down",
            "down": "up",
        }
        return opposites.get(direction.lower(), direction)

    def move_entity(
        self,
        entity: Any,
        to_location_id: str,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> bool:
        """Move an entity to a different location.

        Args:
            entity: Entity to move
            to_location_id: Destination location ID
            x: X coordinate in new location
            y: Y coordinate in new location

        Returns:
            True if entity was moved
        """
        # Remove from current location
        current = self.get_current_location()
        if current and entity in current.entities:
            current.remove_entity(entity)

        # Add to new location
        new_location = self.get_location(to_location_id)
        if new_location:
            new_location.add_entity(entity, x, y)
            return True

        return False

    def save(self) -> Dict[str, Any]:
        """Save world state.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "current_location_id": self.current_location_id,
            "metadata": self.metadata,
            # Locations would need custom serialization for full save
        }

    def load(self, data: Dict[str, Any]) -> None:
        """Load world state.

        Args:
            data: Saved world data
        """
        self.current_location_id = data.get("current_location_id")
        self.metadata = data.get("metadata", {})
