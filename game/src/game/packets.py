from common.network import register_packets
from game.lobby import (
    JoinGameRequest,
    JoinGameResponse,
    PlayerJoined,
    PlayerLeft,
    StartGameRequest,
)

register_packets(
    [JoinGameRequest, JoinGameResponse, StartGameRequest, PlayerJoined, PlayerLeft]
)
