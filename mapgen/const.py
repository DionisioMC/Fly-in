from enum import Enum


class ZoneType(Enum):
    """Represent the different types of zones available on the map."""
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class MovementCosts(Enum):
    """Define the movement costs associated with each zone type."""
    NORMAL = 10
    PRIORITY = 9
    RESTRICTED = 20
