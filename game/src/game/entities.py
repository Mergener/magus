from enum import Enum

# The following enum matches exactly the names in "assets/scenes/server/game.json"'s
# NetworkEntityManager template dict.


class Entities(Enum):
    GAME_MANAGER = "game_manager"
    PLAYER = "player"
    MAGE = "mage"
