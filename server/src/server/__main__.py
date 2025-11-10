import traceback
from sys import stderr

from common import init_common
from common.game import Game
from common.network import NetPeer
from common.packets import JoinGameRequest, JoinGameResponse
from server.netserver import NetServer


def handle_join_request(join_req: JoinGameRequest, peer: NetPeer):
    print(f"{peer.address} asked to join the game!")
    peer.send(JoinGameResponse())


if __name__ == "__main__":
    init_common()

    network = NetServer(port=16214)
    network.listen(JoinGameRequest, handle_join_request)

    game = Game(network=network)
    game.initialize()

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
