from common.network import register_packets
from game.lobby import (
    DoneLoadingGameScene,
    JoinGameRequest,
    JoinGameResponse,
    PlayerJoined,
    PlayerLeft,
    StartGameRequest,
)
from game.mage import MoveToOrder
from game.spells.fireball_projectile import FireballBurst

register_packets(
    [
        JoinGameRequest,
        JoinGameResponse,
        StartGameRequest,
        PlayerJoined,
        PlayerLeft,
        DoneLoadingGameScene,
        MoveToOrder,
        FireballBurst,
    ]
)
