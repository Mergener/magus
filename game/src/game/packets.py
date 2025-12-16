from common.network import register_packets
from game.game_manager import GameFinished, RoundFinished, RoundStarting
from game.lobby_base import (
    DoneLoadingGameScene,
    JoinGameRequest,
    JoinGameResponse,
    LobbyInfoPacket,
    PlayerJoined,
    PlayerLeft,
    RequestLobbyInfo,
    StartGameRequest,
    UpdateLobbyRequest,
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
        RoundStarting,
        RoundFinished,
        RequestLobbyInfo,
        UpdateLobbyRequest,
        LobbyInfoPacket,
        GameFinished,
    ]
)
