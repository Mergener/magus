from enum import Enum

# The following enum matches exactly the names in "assets/scenes/server/game.json"'s
# NetworkEntityManager template dict.


class Entities(Enum):
    PLAYER = ("player",)
    MAGE = "mage"
