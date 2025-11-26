import pygame as pg

from client.scenes.lobby import Lobby
from common.behaviours.ui.canvas import Canvas
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import UILabel
from common.node import Node
from scene_builder.base import save_node


def build_client_scenes():
    build_lobby_menu()


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
    exit_button.label.text = "Exit"
    exit_button.image.image_path = "img/ui/button.png"
    exit_button.node.transform.position = pg.Vector2(0, -100)
    exit_button.image.surface_scale = pg.Vector2(3, 1)

    lobby_menu.add_behaviour(Lobby)

    save_node(lobby_menu, "scenes/client/lobby.json")
