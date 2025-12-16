import pygame as pg

from common.behaviours.animator import Animator
from common.behaviours.network_behaviour import (
    NetworkBehaviour,
    client_method,
    entity_packet_handler,
    server_method,
)
from common.behaviours.network_entity import EntityPacket
from common.behaviours.physics_object import Collision, CollisionHandler, PhysicsObject
from common.network import DeliveryMode, NetPeer
from common.primitives import Vector2
from game.animator_synchronizer import AnimatorSynchronizer
from game.mage import Mage
from game.player import Player


class FireballProjectile(NetworkBehaviour, CollisionHandler):
    caster: Mage
    speed: float
    damage: float
    destination = Vector2()
    duration: float
    hit_force: float

    def on_init(self):
        self._burst = False
        self._animator = None
        self._phys_obj = None
        self._animator = self.node.get_behaviour(Animator)
        self.node.get_or_add_behaviour(AnimatorSynchronizer)

    @property
    def owner(self):
        return self.caster.owner

    def on_server_pre_start(self):
        self._phys_obj = self.node.get_or_add_behaviour(PhysicsObject)
        self._phys_obj.trigger = True
        self._motion = (
            self.destination - self.transform.position
        ).normalize() * self.speed
        self._burst = False
        self._collided = False

    @server_method
    async def on_collision_enter(self, collision: Collision):
        if self._collided:
            return

        if self._burst:
            return

        if self.caster.node is collision.other_collider.node:
            return

        hit_mage = collision.other_collider.node.get_behaviour(Mage)
        if not hit_mage:
            return

        if hit_mage.owner.is_ally_of(self.caster.owner):
            return

        assert self.game

        self._collided = True

        hit_mage.take_damage(self.damage, self.owner)
        impulse = (
            hit_mage.transform.position - self.transform.position
        ).normalize() * self.hit_force
        hit_mage.physics_object.knock_back(impulse)

        await self._do_burst()

    async def _do_burst(self):
        assert self.game

        if self._burst:
            return

        self._burst = True
        if self._animator is not None:
            self._animator.play("burst")
            self._animator.enqueue("null")

        if self._phys_obj:
            self._phys_obj.collider.disabled = True

        await self.game.simulation.wait_seconds(2)
        self.node.destroy()

    async def on_client_start(self):
        if not self._animator:
            return

        self._animator.play("spawn")
        self._animator.enqueue("idle")

    async def on_server_start(self):
        assert self.game
        direction = self.destination - self.transform.position

        pg_dir = Vector2(direction.x, direction.y)

        self.transform.rotation = Vector2(1, 0).angle_to(pg_dir)

        await self.game.simulation.wait_seconds(self.duration)

        await self._do_burst()

    def on_server_tick(self, tick_id: int):
        assert self.game
        assert self._phys_obj

        if self._burst:
            return

        tick_interval = self.game.simulation.tick_interval
        self._phys_obj.move_and_collide(self._motion * tick_interval)
