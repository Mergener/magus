import pygame as pg


def overrides_method(base_class: type, instance: object, method_name: str):
    base_method = getattr(base_class, method_name)
    instance_method = getattr(instance.__class__, method_name)
    return instance_method is not base_method


def memberwise_multiply(v1: pg.Vector2, v2: pg.Vector2):
    return pg.Vector2(v1.x * v2.x, v1.y * v2.y)