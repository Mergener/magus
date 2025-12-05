import pygame as pg

from game.spell import SpellState
from game.spells.fireball_projectile import FireballProjectile


class FireballState(SpellState):
    def on_point_cast(self, target: pg.Vector2):
        entity = self.entity_manager.spawn_entity("fireball_projectile")
        entity.transform.position = self.transform.position
        projectile = entity.node.get_or_add_behaviour(FireballProjectile)
        projectile.speed = self.spell.data.get("projectile_speed", 800)
        projectile.destination = target
