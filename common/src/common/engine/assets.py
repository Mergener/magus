import copy
import json
import os
import sys
import traceback
from abc import ABC, abstractmethod
from sys import stderr
from typing import TYPE_CHECKING

import pygame as pg

from common.engine.node import Node

if TYPE_CHECKING:
    from common.engine.animation import Animation


class ImageAsset:
    def __init__(
        self,
        pygame_surface: pg.Surface,
        path: str | None = None,
        rect: pg.Rect | None = None,
    ):
        self.pygame_surface = pygame_surface or _get_placeholder_surface()
        self.path = path
        self.rect = rect or self.pygame_surface.get_rect()

    def serialize(self, out_dict: dict | None = None):
        if not out_dict:
            out_dict = {}

        out_dict["path"] = self.path
        rect = self.rect or self.pygame_surface.get_rect()
        out_dict["rect"] = {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h}
        return out_dict

    def deserialize(self, in_dict: dict):
        path = in_dict.get("path")
        self.pygame_surface = load_image_asset(path or "").pygame_surface

        rect = in_dict.get("rect")
        if rect is not None:
            x = rect.get("x")
            y = rect.get("y")
            w = rect.get("w")
            h = rect.get("h")
            if (
                (type(x) == float or type(x) == int)
                and (type(y) == float or type(y) == int)
                and (type(w) == float or type(w) == int)
                and (type(h) == float or type(h) == int)
            ):
                self.rect = pg.Rect((x, y), (w, h))
                sliced_surface = self.pygame_surface.subsurface(self.rect)
                self.pygame_surface = sliced_surface
            else:
                self.rect = self.pygame_surface.get_rect()
        else:
            self.rect = self.pygame_surface.get_rect()
        return self


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)


def load_image_asset(path: str) -> ImageAsset:
    full_path = None
    try:
        full_path = resource_path(path)

        cached = _image_asset_cache.get(full_path)
        if cached:
            return cached

        surface = pg.image.load(full_path).convert_alpha()
        if surface is None:
            raise Exception("Image not found.")

        image_asset = ImageAsset(surface, path)
        _image_asset_cache[full_path] = image_asset
        return image_asset
    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(f"Failed to load image from {path}: {error_stack_trace}", file=stderr)
        fallback = ImageAsset(_get_placeholder_surface())
        _image_asset_cache[full_path or path] = fallback
        return fallback


def load_node_asset(path: str) -> Node:
    full_path = None
    try:
        full_path = resource_path(path)

        cached = _node_asset_cache.get(full_path)
        if cached:
            return cached.clone()

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        node = Node().deserialize(data)

        _node_asset_cache[full_path] = node
        return node
    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(f"Failed to load node from {path}: {error_stack_trace}", file=stderr)

        fallback = Node()
        _node_asset_cache[full_path or path] = fallback.clone()
        return fallback


def load_animation_asset(path: str):
    from common.engine.animation import Animation

    full_path = None

    try:
        full_path = resource_path(path)

        cached = _animation_asset_cache.get(full_path)
        if cached:
            return cached

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        animation = Animation.__new__(Animation).deserialize(data)

        _animation_asset_cache[full_path] = animation
        return animation
    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(f"Failed to load animation from {path}: {error_stack_trace}", file=stderr)
        fallback = Animation([], 1)
        _animation_asset_cache[full_path or path] = fallback
        return fallback


def _get_placeholder_surface():
    placeholder_texture = pg.Surface((100, 100))
    placeholder_texture.fill((0, 255, 0))
    return placeholder_texture


_node_asset_cache: dict[str, Node] = {}
_image_asset_cache: dict[str, ImageAsset] = {}
_animation_asset_cache: dict[str, Animation] = {}
