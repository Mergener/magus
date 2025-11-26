import asyncio
import traceback
from sys import stderr

from common.assets import load_node_asset
from common.game import Game
from server.netserver import NetServer


async def main():
    network = NetServer(port=16214)

    game = Game(network=network, scene=load_node_asset("scenes/server/lobby.json"))

    running = True
    while running:
        try:
            await game.iterate()
        except KeyboardInterrupt:
            running = False
        except Exception as _:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)
    game.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
