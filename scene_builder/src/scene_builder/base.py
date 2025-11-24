import json

from common.assets import resource_path
from common.node import Node


def save_node(node: Node, path: str):
    with open(resource_path(path), "w") as f:
        f.write(json.dumps(node.serialize()))
