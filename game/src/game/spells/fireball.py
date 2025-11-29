import pygame as pg

from game.spell import SpellState, get_spell


class FireballState(SpellState):
    def on_point_cast(self, target: pg.Vector2):
        print(f"Fireball cast towards {target}")
