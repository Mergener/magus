from common.node import Node
from scene_builder.base import save_node


def build_fireball_projectile():
    fireball_projectile = Node()

    save_node(fireball_projectile, "templates/spells/fireball_projectile.json")
