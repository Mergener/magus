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
from game.mage import Mage


class FireballBurst(EntityPacket):
    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE


class FireballProjectile(NetworkBehaviour, CollisionHandler):
    caster: Mage
    speed: float
    destination = Vector2()
    _owner_index: int

    def on_init(self):
        self._burst = False
        self._animator = None

    def on_server_pre_start(self):
        self._phys_obj = self.node.get_or_add_behaviour(PhysicsObject)
        self._motion = (
            self.destination - self.transform.position
        ).normalize() * self.speed
        self._burst = False

    @server_method
    async def on_collision_enter(self, collision: Collision):
        if self.caster.node is collision.other_collider.node:
            return

        assert self.game
        self.game.network.publish(FireballBurst(self.net_entity.id))
        await self._do_burst()

    @entity_packet_handler(FireballBurst)
    @client_method
    async def _handle_burst(self, fireball_burst: FireballBurst, peer: NetPeer):
        await self._do_burst()

    async def _do_burst(self):
        assert self.game

        if self._burst:
            return

        self._burst = True
        if self._animator is not None:
            self._animator.play("burst")
            self._animator.enqueue("null")

        await self.game.simulation.wait_seconds(2)
        self.node.destroy()

    def on_client_pre_start(self):
        self._animator = self.node.get_behaviour(Animator)

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

    def on_server_tick(self, tick_id: int):
        assert self.game

        tick_interval = self.game.simulation.tick_interval
        self._phys_obj.move_and_collide(self._motion * tick_interval)
