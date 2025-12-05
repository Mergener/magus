import json
import os

from common.animation import Animation
from common.assets import resource_path
from common.node import Node


def save_node(node: Node, path: str):
    path = resource_path(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(node.serialize()))


def save_animation(animation: Animation):
    path = resource_path(animation.path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(animation.serialize()))
