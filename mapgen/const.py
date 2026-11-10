from enum import Enum


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class MovementCosts(Enum):
    NORMAL = 10
    PRIORITY = 9
    RESTRICTED = 20
