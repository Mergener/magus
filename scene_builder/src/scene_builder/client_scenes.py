import json

import pygame as pg

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
from common.behaviours.physics_object import PhysicsObject
from common.behaviours.ui.canvas import Canvas
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import UILabel
from common.node import Node
from game.mage import Mage
from scene_builder.base import save_node


def build_client_scenes():
    build_main_menu()
    build_lobby_menu()
    build_mage_template()


def build_main_menu():
    lobby_menu = Node(name="Main Menu")
    canvas = lobby_menu.add_behaviour(Canvas)

    lobby_label = lobby_menu.add_child().add_behaviour(UILabel)
    lobby_label.text = "Magus"
    lobby_label.bold = True
    lobby_label.font_size = 50
    lobby_label.node.transform.position = pg.Vector2(0, 100)

    play_button = lobby_menu.add_child().add_behaviour(UIButton)
    play_button.label.text = "Play"
    play_button.image.image_path = "img/ui/button.png"
    play_button.image.surface_scale = pg.Vector2(3, 1)
    play_button.image.transform.position = pg.Vector2(0, 0)

    exit_button = lobby_menu.add_child().add_behaviour(UIButton)
    exit_button.label.text = "Exit"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = pg.Vector2(0, -100)
    exit_button.image.surface_scale = pg.Vector2(3, 1)

    lobby_menu.add_behaviour(MainMenu)

    save_node(lobby_menu, "scenes/client/main_menu.json")


def build_lobby_menu():
    lobby_menu = Node(name="lobby")
    canvas = lobby_menu.add_behaviour(Canvas)

    lobby_label = lobby_menu.add_child().add_behaviour(UILabel)
    lobby_label.text = "Lobby"
    lobby_label.bold = True
    lobby_label.font_size = 36
    lobby_label.node.transform.position = pg.Vector2(0, 100)

    play_button = lobby_menu.add_child().add_behaviour(UIButton)
    play_button.label.text = "Start"
    play_button.image.image_path = "img/ui/button.png"
    play_button.image.surface_scale = pg.Vector2(3, 1)
    play_button.image.transform.position = pg.Vector2(0, 0)

    exit_button = lobby_menu.add_child().add_behaviour(UIButton)
    exit_button.label.text = "Back"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = pg.Vector2(0, -100)
    exit_button.image.surface_scale = pg.Vector2(3, 1)

    lobby_menu.add_behaviour(Lobby)

    save_node(lobby_menu, "scenes/client/lobby.json")


def build_mage_template():
    mage_node = Node()

    # Make mage animation
    slices = slice_image(
        load_image_asset("img/mage.png"), pg.Vector2(32, 32), SliceMode.SIZE_PER_RECT
    )
    frames = [AnimationFrame(s) for s in slices]
    animation = Animation(frames, path="animations/mage-animation.json")
    with open(resource_path(animation.path), "w") as f:
        json.dump(animation.serialize(), f)

    mage = mage_node.add_behaviour(Mage)
    mage.transform.local_scale = pg.Vector2(1.7, 1.7)
    animator = mage_node.get_or_add_behaviour(Animator)
    animator.animations = {"idle": animation}
    collider = mage_node.add_behaviour(Collider)
    collider.base_shape = RectCollisionShape(pg.Vector2(slices[0].rect.size) / 2)
    # collider.base_shape = CircleCollisionShape(slices[0].rect.size[0])
    mage_node.add_behaviour(PhysicsObject)

    save_node(mage_node, "templates/mage.json")
