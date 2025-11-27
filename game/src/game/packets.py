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

register_packets(
    [
        JoinGameRequest,
        JoinGameResponse,
        StartGameRequest,
        PlayerJoined,
        PlayerLeft,
        DoneLoadingGameScene,
        MoveToOrder,
    ]
)
