import pygame as pg

# import numpy as np

from client.assets import load_image_asset
from enum import Enum

DEFAULT_ANIMATION_FPS = 6


class SliceMode(Enum):
    RECTS_PER_AXIS = 0
    SIZE_PER_RECT = 1


def slice_image(
    img: str | pg.Surface, slicing: pg.Vector2, slice_mode: SliceMode
) -> list[pg.Surface]:
    if not isinstance(img, pg.Surface):
        img = load_image_asset(img)

    if slice_mode == SliceMode.RECTS_PER_AXIS:
        rects_per_axis = slicing
        size_per_rect = pg.Vector2(
            img.get_width() // slicing.x, img.get_height() // slicing.y
        )
    else:
        rects_per_axis = pg.Vector2(
            img.get_width() // slicing.x, img.get_height() // slicing.y
        )
        size_per_rect = slicing

    quads = []
    y = 0.0
    for i in range(int(rects_per_axis.y)):
        x = 0.0
        for j in range(int(rects_per_axis.x)):
            sub_rect = pg.Rect(pg.Vector2(x, y), size_per_rect)
            if is_sub_rect_transparent(img, sub_rect):
                continue

            frame_surface = pg.Surface(size_per_rect, pg.SRCALPHA)
            frame_surface.blit(img, (0, 0), pg.Rect((x, y), size_per_rect))

            quads.append(frame_surface)
            x += size_per_rect.x
        y += size_per_rect.y

    return quads


class AnimationFrame:
    def __init__(self, texture: pg.Surface, speed=1.0):
        self.texture = texture
        self.speed = speed


class Animation:
    def __init__(
        self, frames: list[AnimationFrame], fps: float = DEFAULT_ANIMATION_FPS
    ):
        self.frames = frames
        self.fps = fps


def is_sub_rect_transparent(surface: pg.Surface, rect: pg.Rect) -> bool:
    if surface.get_masks()[3] == 0:
        raise False

    rect = rect.clip(surface.get_rect())
    if rect.width == 0 or rect.height == 0:
        return True

    alpha_array = pg.surfarray.array_alpha(surface)
    sub = alpha_array[rect.left : rect.right, rect.top : rect.bottom]
    return np.all(sub == 0)
