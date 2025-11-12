import traceback
from sys import stderr

from common.engine.game import Game
from common.engine.network import NetPeer, auto_resolve_packets
from common.magus.entity_type import EntityType
from common.magus.packets import CreateEntity, JoinGameRequest, JoinGameResponse
from server.netserver import NetServer


def handle_join_request(join_req: JoinGameRequest, peer: NetPeer):
    peer.send(JoinGameResponse())
    peer.send(CreateEntity(0, EntityType.MAGE))


if __name__ == "__main__":
    auto_resolve_packets()

    network = NetServer(port=16214)
    network.listen(JoinGameRequest, handle_join_request)

    game = Game(network=network)

    running = True
    while running:
        try:
            game.iterate()
        except KeyboardInterrupt:
            running = False
        except Exception as _:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)
    game.cleanup()
