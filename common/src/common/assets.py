import copy
import json
import os
import sys
import traceback
from abc import ABC, abstractmethod
from sys import stderr
from typing import TYPE_CHECKING, Callable, Self

import pygame as pg


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
    global _image_asset_cache

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


class Serializable(ABC):
    @abstractmethod
    def serialize(self, out_dict: dict | None = None) -> dict:
        pass

    @abstractmethod
    def deserialize(self, in_dict: dict) -> Self:
        pass


def load_object_asset[T: Serializable](
    path: str, t: type[T], ctor: Callable[[], T] | None = None
) -> T:
    global _object_asset_cache

    cache = _object_asset_cache.get(t)
    if cache is None:
        cache = {}
        _object_asset_cache[t] = cache

    def create_object():
        if ctor is not None:
            return ctor()
        try:
            obj = t()
            return obj
        except:
            obj = t.__new__(t)
            return obj

    full_path = None
    try:
        full_path = resource_path(path)

        cached = cache.get(full_path)
        if cached:
            return cached

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj = create_object().deserialize(data)

        cache[full_path] = obj
        return obj
    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(
            f"Failed to load {t.__name__} asset from {path}: {error_stack_trace}",
            file=stderr,
        )

        fallback = create_object()
        cache[full_path or path] = fallback
        return fallback


def load_node_asset(path: str):
    from common.node import Node

    return load_object_asset(path, Node).clone()


def load_animation_asset(path: str):
    from common.animation import Animation

    global _animation_asset_cache

    full_path = None

    try:
        full_path = resource_path(path)

        cached = _animation_asset_cache.get(full_path)
        if cached:
            return cached

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        animation = Animation.__new__(Animation).deserialize(data)
        animation.path = full_path

        _animation_asset_cache[full_path] = animation
        return animation
    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(f"Failed to load animation from {path}: {error_stack_trace}", file=stderr)
        fallback = Animation([], 1)
        _animation_asset_cache[full_path or path] = fallback
        return fallback


def load_font_asset(
    font_name: str, font_size: int, bold: bool = False, italic: bool = False
):
    global _font_asset_cache

    cache_key = (font_name, font_size, bold, italic)

    try:
        cached = _font_asset_cache.get(cache_key)
        if cached:
            return cached

        if font_name:
            full_path = resource_path(font_name)
            try:
                font = pg.font.Font(full_path, font_size)
            except FileNotFoundError as e:
                # User might be expecting a system font.
                font = pg.font.SysFont(font_name, font_size)
        else:
            font = pg.font.SysFont("Arial", font_size)

        font.set_bold(bold)
        font.set_italic(italic)

        _font_asset_cache[cache_key] = font
        return font

    except Exception as e:
        error_stack_trace = traceback.format_exc()
        print(
            f"Failed to load font {font_name} (size {font_size}, bold={bold}, italic={italic}): {error_stack_trace}",
            file=stderr,
        )

        fallback = pg.font.Font(None, font_size)
        _font_asset_cache[cache_key] = fallback
        return fallback


def _get_placeholder_surface():
    placeholder_texture = pg.Surface((100, 100))
    placeholder_texture.fill((0, 255, 0))
    return placeholder_texture


_object_asset_cache = {}  # type: ignore
_image_asset_cache = {}  # type: ignore
_animation_asset_cache = {}  # type: ignore
_font_asset_cache = {}  # type: ignore
