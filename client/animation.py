import pygame as pg
# import numpy as np

from client.assets import load_image_asset
from enum import Enum

DEFAULT_ANIMATION_FPS = 6

class SliceMode(Enum):
    RECTS_PER_AXIS = 0
    SIZE_PER_RECT = 1

class AnimationFrame:
    def __init__(self, texture: pg.Surface, speed = 1.0):
        self.texture = texture
        self.speed = speed
        
class Animation:
    def __init__(self, frames: list[AnimationFrame], fps: float = DEFAULT_ANIMATION_FPS):
        self.frames = frames
        self.fps = fps
        
    @classmethod
    def from_spritesheet(cls, asset: str | pg.Surface, slice_dimensions: pg.Vector2, slice_mode: SliceMode, fps: float = DEFAULT_ANIMATION_FPS):
        if not isinstance(asset, pg.Surface):
            asset = load_image_asset(asset)
        
        if slice_mode == SliceMode.RECTS_PER_AXIS:
            rects_per_axis = slice_dimensions
            slice_dimensions = pg.Vector2(asset.get_width() / slice_dimensions.x, asset.get_height() / slice_dimensions.y)
        else:
            rects_per_axis = pg.Vector2(asset.get_width() // slice_dimensions.x, asset.get_height() // slice_dimensions.y)
            
        frames = []
        y = 0
        for i in range(int(rects_per_axis.y)):
            x = 0            
            for j in range(int(rects_per_axis.x)):
                sub_rect = pg.Rect(pg.Vector2(x, y), slice_dimensions)
                if is_sub_rect_transparent(asset, sub_rect):
                    continue
                
                frame_surface = pg.Surface(slice_dimensions, pg.SRCALPHA)
                frame_surface.blit(asset, (0, 0), pg.Rect((x, y), slice_dimensions))
                
                frames.append(AnimationFrame(frame_surface))
                x += slice_dimensions.x
            y += slice_dimensions.y
        
        return Animation(frames, fps)


def is_sub_rect_transparent(surface: pg.Surface, rect: pg.Rect) -> bool:
    return False
    if surface.get_masks()[3] == 0:
        raise ValueError("Surface has no alpha channel")

    rect = rect.clip(surface.get_rect())
    if rect.width == 0 or rect.height == 0:
        return True 

    alpha_array = pg.surfarray.array_alpha(surface)
    sub = alpha_array[rect.left:rect.right, rect.top:rect.bottom]
    return np.all(sub == 0) 