from enum import Enum
import random


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


class Colors(Enum):
    """Define ANSI escape codes for terminal text colors and formatting.

    Provides standard and extended terminal colors, as well as special
    values for rainbow and default terminal formatting.
    """
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[34m"
    YELLOW = "\033[93m"
    ORANGE = "\033[38;5;208m"
    CYAN = "\033[96m"
    PURPLE = "\033[35m"
    MAGENTA = "\033[35m"
    BROWN = "\033[38;5;94m"
    LIME = "\033[38;5;118m"
    GOLD = "\033[38;5;220m"
    BLACK = "\033[30m"
    MAROON = "\033[38;5;52m"
    DARKRED = "\033[38;5;88m"
    VIOLET = "\033[38;5;129m"
    CRIMSON = "\033[38;5;161m"
    RAINBOW = "RAINBOW"
    WHITE = "\033[0m"
    END = "\033[0m"
    DEFAULT = "\033[0m"

    @classmethod
    def random_color(cls) -> "Colors":
        """Select a random color from the available terminal colors.

        Excludes special values that do not represent actual colors,
        such as RAINBOW, WHITE, END, and DEFAULT.

        Returns:
            Colors: A randomly selected color enum member.
        """
        colors = [
            color for color in cls
            if color not in (cls.RAINBOW, cls.WHITE, cls.END, cls.DEFAULT)
        ]
        return random.choice(colors)
