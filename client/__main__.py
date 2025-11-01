import pygame as pg

from sys import stderr

from client.animation import Animation, SliceMode
from client.assets import load_image_asset
from client.behaviours.animator import Animator
from client.behaviours.player import Player
from client.behaviours.sprite_renderer import SpriteRenderer
from client.netclient import NetClient
from common import init_common
from common.enums import DeliveryMode
from common.simulation import Node, Simulation

def create_scene(simulation) -> Node:
    scene = Node()
    
    img = load_image_asset("img/mage_a_walking.png")
    
    sprite_renderer = SpriteRenderer(img)
    scene.add_behaviour(sprite_renderer)
    
    animation = Animation.from_spritesheet(img, pg.Vector2(4, 8), SliceMode.RECTS_PER_AXIS)
    animation.frames = animation.frames[16:20]
    scene.add_behaviour(Animator(animation))
    scene.add_behaviour(Player())
    
    scene.simulation = simulation

if __name__ == "__main__":
    init_common()
    pg.init()
    
    window = pg.display.set_mode((1280, 720))
    # net_client = NetClient("localhost", 9999)
    simulation = Simulation()
    create_scene(simulation)
    
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
            
            window.fill((0, 0, 0))
            simulation.render(window)
            pg.display.flip()
            
        except Exception as e:
            print(f"Error: {e}", file=stderr)