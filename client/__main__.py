import traceback
from sys import stderr

import pygame as pg

from client.netclient import NetClient
from common import init_common
from common.packets import NewGame
from common.simulation import Simulation

if __name__ == "__main__":
    init_common()
    pg.init()

    window = pg.display.set_mode((1280, 720))

    simulation = Simulation()

    network = NetClient("localhost", 16214)
    network.publish(NewGame())

    running = True
    last_tick = 0
    while running:
        try:
            this_tick = pg.time.get_ticks()
            dt = (this_tick - last_tick) / 1000.0
            last_tick = this_tick

            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False

            simulation.update(dt)

            network.poll()

            window.fill("white")
            simulation.render()
            pg.display.flip()

        except:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)

    network.disconnect()
