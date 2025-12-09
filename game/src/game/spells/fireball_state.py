import pygame as pg

from common.primitives import Vector2
from game.spell import SpellState
from game.spells.fireball_projectile import FireballProjectile


class FireballState(SpellState):
    def on_point_cast(self, target: Vector2):
        entity = self.entity_manager.spawn_entity("fireball_projectile")
        entity.transform.position = self.transform.position
        projectile = entity.node.get_or_add_behaviour(FireballProjectile)
        projectile.speed = self.get_current_level_data("projectile_speed", 800)
        projectile.caster = self._mage
        projectile.destination = target
        projectile.damage = self.get_current_level_data("damage", 0.0)
