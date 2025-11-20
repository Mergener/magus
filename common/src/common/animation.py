from __future__ import annotations

from enum import Enum
from typing import cast

import numpy as np
import pygame as pg

from common.assets import ImageAsset

DEFAULT_ANIMATION_FPS = 6


class SliceMode(Enum):
    RECTS_PER_AXIS = 0
    SIZE_PER_RECT = 1


def slice_image(
    img: ImageAsset, slicing: pg.Vector2, slice_mode: SliceMode, copy: bool = False
) -> list[ImageAsset]:
    surface = img.pygame_surface
    if slice_mode == SliceMode.RECTS_PER_AXIS:
        rects_per_axis = slicing
        size_per_rect = pg.Vector2(
            surface.get_width() // slicing.x, surface.get_height() // slicing.y
        )
    else:
        rects_per_axis = pg.Vector2(
            surface.get_width() // slicing.x, surface.get_height() // slicing.y
        )
        size_per_rect = slicing

    quads: list[ImageAsset] = []
    y = 0.0
    for i in range(int(rects_per_axis.y)):
        x = 0.0
        for j in range(int(rects_per_axis.x)):
            sub_rect = pg.Rect(pg.Vector2(x, y), size_per_rect)
            if is_sub_rect_transparent(surface, sub_rect):
                continue

            frame_surface = surface.subsurface(sub_rect)
            if copy:
                frame_surface = frame_surface.copy()

            quads.append(
                ImageAsset(frame_surface, img.path, pg.Rect((x, y), size_per_rect))
            )
            x += size_per_rect.x
        y += size_per_rect.y

    return quads


class AnimationFrame:
    def __init__(self, image: ImageAsset, speed=1.0):
        self.image = image
        self.speed = speed

    def serialize(self, out_dict: dict | None = None):
        if out_dict is None:
            out_dict = {}

        out_dict["image"] = self.image.serialize()
        out_dict["speed"] = self.speed

        return out_dict

    def deserialize(self, in_dict: dict):
        self.image = ImageAsset.__new__(ImageAsset).deserialize(
            in_dict.get("image", {})
        )
        self.speed = in_dict.get("speed", 1)
        return self


class Animation:
    def __init__(
        self,
        frames: list[AnimationFrame],
        fps: float = DEFAULT_ANIMATION_FPS,
        path: str | None = None,
    ):
        self.frames = frames
        self.fps = fps
        self.path = path or ""

    def serialize(self, out_dict: dict | None = None) -> dict:
        if out_dict is None:
            out_dict = {}

        frames = []
        for f in self.frames:
            frames.append(f.serialize())
        out_dict["frames"] = frames
        out_dict["fps"] = self.fps

        return out_dict

    def deserialize(self, in_value: dict) -> Animation:
        self.frames = [
            AnimationFrame.__new__(AnimationFrame).deserialize(d)
            for d in in_value.get("frames", [])
        ]
        self.fps = in_value.get("fps", DEFAULT_ANIMATION_FPS)
        self.path = ""
        return self


def is_sub_rect_transparent(surface: pg.Surface, rect: pg.Rect) -> bool:
    if surface.get_masks()[3] == 0:
        return False

    rect = rect.clip(surface.get_rect())
    if rect.width == 0 or rect.height == 0:
        return True

    alpha_array = pg.surfarray.array_alpha(surface)
    sub = alpha_array[rect.left : rect.right, rect.top : rect.bottom]
    return bool(np.all(sub == 0))
