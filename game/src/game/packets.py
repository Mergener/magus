from common.network import register_packets
from game.lobby import JoinGameRequest, JoinGameResponse, PlayerJoined, StartGameRequest

register_packets([JoinGameRequest, JoinGameResponse, StartGameRequest, PlayerJoined])
