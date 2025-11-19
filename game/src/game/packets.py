from common.network import register_packets
from game.match import JoinGameRequest, JoinGameResponse, NewGame, PlayerJoined

register_packets([JoinGameRequest, JoinGameResponse, NewGame, PlayerJoined])
