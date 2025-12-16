import json

import pygame as pg

from client.hud import Hud
from client.scenes.game_over_menu import GameOverMenu
from client.scenes.lobby import Lobby
from client.scenes.main_menu import MainMenu
from common.animation import Animation, AnimationFrame, SliceMode, slice_image
from common.assets import load_image_asset, resource_path
from common.behaviours.animator import Animator
from common.behaviours.collider import (
    CircleCollisionShape,
    Collider,
    RectCollisionShape,
)
from common.behaviours.network_entity import NetworkEntity
from common.behaviours.physics_object import PhysicsObject
from common.behaviours.sprite_renderer import SpriteRenderer
from common.behaviours.tilemap import Tilemap
from common.behaviours.ui.canvas import Canvas
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import HorizontalAlign, UILabel
from common.node import Node
from common.primitives import Vector2
from common.utils import notnull
from game.mage import Mage
from game.ui.status_bar import StatusBar
from scene_builder.base import save_animation, save_node


def build_client_scenes():
    build_main_menu()
    build_lobby_menu()
    build_mage_template()
    build_hud()
    build_end_menu()
    # build_world()


def build_main_menu():
    lobby_menu = Node(name="Main Menu")
    canvas = lobby_menu.add_behaviour(Canvas)

    lobby_label = lobby_menu.add_child().add_behaviour(UILabel)
    lobby_label.text = "Magus"
    lobby_label.bold = True
    lobby_label.font_size = 50
    lobby_label.node.transform.position = Vector2(0, 100)

    play_button = lobby_menu.add_child().add_behaviour(UIButton)
    play_button.label.text = "Play"
    play_button.image.image_path = "img/ui/button.png"
    play_button.image.surface_scale = Vector2(3, 1)
    play_button.image.transform.position = Vector2(0, 0)

    exit_button = lobby_menu.add_child().add_behaviour(UIButton)
    exit_button.label.text = "Exit"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = Vector2(0, -100)
    exit_button.image.surface_scale = Vector2(3, 1)

    lobby_menu.add_behaviour(MainMenu)

    save_node(lobby_menu, "scenes/client/main_menu.json")


def build_lobby_menu():
    lobby_menu = Node(name="lobby")
    canvas = lobby_menu.add_behaviour(Canvas)

    lobby_label = lobby_menu.add_child().add_behaviour(UILabel)
    lobby_label.text = "Lobby"
    lobby_label.bold = True
    lobby_label.font_size = 36
    lobby_label.node.transform.position = Vector2(0, 100)

    play_button = lobby_menu.add_child().add_behaviour(UIButton)
    play_button.label.text = "Start"
    play_button.image.image_path = "img/ui/button.png"
    play_button.image.surface_scale = Vector2(3, 1)
    play_button.image.transform.position = Vector2(0, 0)

    exit_button = lobby_menu.add_child().add_behaviour(UIButton)
    exit_button.label.text = "Back"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = Vector2(0, -100)
    exit_button.image.surface_scale = Vector2(3, 1)

    lobby_info_label = lobby_menu.add_child().add_behaviour(UILabel)
    lobby_info_label.text = ""
    lobby_info_label.bold = False
    lobby_info_label.font_size = 24
    lobby_info_label.anchor = Vector2(0.1, 0.95)
    lobby_info_label.horizontal_align = HorizontalAlign.LEFT
    # lobby_info_label.transform.position = Vector2(-1500, 500)

    lobby_menu.add_behaviour(Lobby)

    save_node(lobby_menu, "scenes/client/lobby.json")


def build_end_menu():
    end_menu = Node(name="end_menu")
    canvas = end_menu.add_behaviour(Canvas)

    lobby_label = end_menu.add_child().add_behaviour(UILabel)
    lobby_label.text = "Game Over!"
    lobby_label.bold = False
    lobby_label.font_size = 36
    lobby_label.node.transform.position = Vector2(0, 200)

    winner_label = end_menu.add_child().add_behaviour(UILabel)
    winner_label.text = f"Team X Victory!"
    winner_label.bold = True
    winner_label.font_size = 46
    winner_label.node.transform.position = Vector2(0, 120)

    exit_button = end_menu.add_child().add_behaviour(UIButton)
    exit_button.label.text = "Back"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = Vector2(0, -50)
    exit_button.image.surface_scale = Vector2(3, 1)

    end_menu.add_behaviour(GameOverMenu)

    save_node(end_menu, "scenes/client/end_menu.json")


def build_mage_template():
    mage_node = Node()

    # Make mage animations
    animation_names = ["idle", "move", "die", "cast"]
    animation_dict = {}
    for anim in animation_names:
        slices = slice_image(
            load_image_asset(f"img/mage/mage-{anim}.png"),
            Vector2(64, 64),
            SliceMode.SIZE_PER_RECT,
        )
        frames = [AnimationFrame(s) for s in slices]
        animation = Animation(
            frames, path=f"animations/mage-animation-{anim}.json", fps=20
        )
        animation_dict[anim] = animation

        if anim == "idle":
            animation.frames = frames[0:2]
            animation.fps = 1
        elif anim == "die":
            animation.frames[-1].speed = 0.08

        save_animation(animation)

    mage = mage_node.add_behaviour(Mage)
    mage.transform.local_scale = Vector2(1.1, 1.1)
    animator = mage_node.add_child().get_or_add_behaviour(Animator)
    animator.node.add_behaviour(NetworkEntity)
    animator.animations = animation_dict

    collider = mage_node.get_or_add_behaviour(Collider)
    collider.base_shape = RectCollisionShape(Vector2(32, 32))
    mage_node.get_or_add_behaviour(PhysicsObject)

    health_bar_node = mage_node.add_child()
    health_bar_node.transform.local_position += Vector2(0, 70)
    health_bar = health_bar_node.add_behaviour(StatusBar)
    health_bar.image_scale = Vector2(4, 1)

    save_node(mage_node, "templates/mage.json")


def build_hud():
    hud_node = Node()

    hud = hud_node.get_or_add_behaviour(Hud)
    scoreboard = hud_node.add_child().add_behaviour(UILabel)
    scoreboard.text = "Scoreboard"
    scoreboard.horizontal_align = HorizontalAlign.LEFT
    scoreboard.font_size = 14
    scoreboard.anchor = Vector2(0.93, 0.93)

    save_node(hud_node, "templates/hud.json")


# def build_world():
#     world_node = Node()

#     tileset_asset = load_image_asset("img/tileset.png")
#     upper = tileset_asset
#     # for i in range(2):
#     #     upper = slice_image(upper, Vector2(1, 2), SliceMode.RECTS_PER_AXIS)[0]

#     tiles = slice_image(upper, Vector2(32, 32), SliceMode.SIZE_PER_RECT)
#     tilemap = world_node.add_behaviour(Tilemap)

#     with tilemap.edit():
#         tilemap.tileset = tiles
#         tilemap.dimensions = (20, 20)
#         x = 0
#         for i in range(20):
#             for j in range(20):
#                 tilemap.set_tile_at((i, j), x + 1)
#                 x = (x + 1) % 2

#     save_node(world_node, "templates/world.json")
