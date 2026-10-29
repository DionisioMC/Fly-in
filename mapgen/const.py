from enum import Enum


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class MovementCosts(Enum):
    NORMAL = 1
    PRIORITY = 1
    RESTRICTED = 2
    BLOCKED = -1
    DEFAULT = 1
