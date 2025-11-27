from time import monotonic

import pygame as pg


class Input:
    def __init__(self):
        self.double_click_time = 0.40
        self.drag_threshold = 3

        self._keys_just_pressed: list[int] = []
        self._keys_just_released: list[int] = []

        self._mouse_buttons_just_pressed: list[tuple[int, bool]] = []
        self._mouse_buttons_just_released: list[int] = []

        self._mouse_pos = (0, 0)
        self._last_mouse_pos = (0, 0)
        self._mouse_delta = (0, 0)

        self._scroll_delta = (0, 0)

        self._last_click_time = {}

        self._drag_start_pos = {}
        self._is_dragging = {}

    def handle_pygame_events(self, events: list[pg.event.Event]):
        self._keys_just_pressed.clear()
        self._keys_just_released.clear()
        self._mouse_buttons_just_pressed.clear()
        self._mouse_buttons_just_released.clear()
        self._scroll_delta = (0, 0)

        must_stop = False

        for ev in events:
            if ev.type == pg.QUIT:
                must_stop = True

            elif ev.type == pg.KEYDOWN:
                if ev.key not in self._keys_just_pressed:
                    self._keys_just_pressed.append(ev.key)

            elif ev.type == pg.KEYUP:
                if ev.key not in self._keys_just_released:
                    self._keys_just_released.append(ev.key)

            elif ev.type == pg.MOUSEBUTTONDOWN:
                self._mouse_buttons_just_pressed.append((ev.button, False))

                now = monotonic()
                last = self._last_click_time.get(ev.button, 0.0)
                if now - last <= self.double_click_time:
                    self._mouse_buttons_just_pressed.append((ev.button, True))
                self._last_click_time[ev.button] = now

                self._drag_start_pos[ev.button] = ev.pos
                self._is_dragging[ev.button] = False

            elif ev.type == pg.MOUSEBUTTONUP:
                self._mouse_buttons_just_released.append(ev.button)
                if ev.button in self._is_dragging:
                    del self._is_dragging[ev.button]
                if ev.button in self._drag_start_pos:
                    del self._drag_start_pos[ev.button]

            elif ev.type == pg.MOUSEWHEEL:
                self._scroll_delta = (ev.x, ev.y)

        self._last_mouse_pos = self._mouse_pos
        self._mouse_pos = pg.mouse.get_pos()
        self._mouse_delta = (
            self._mouse_pos[0] - self._last_mouse_pos[0],
            self._mouse_pos[1] - self._last_mouse_pos[1],
        )

        for btn, start_pos in list(self._drag_start_pos.items()):
            if btn in self.get_pressed_mouse_buttons():
                dx = self._mouse_pos[0] - start_pos[0]
                dy = self._mouse_pos[1] - start_pos[1]
                if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
                    self._is_dragging[btn] = True

        return must_stop

    def is_key_pressed(self, key: int):
        return pg.key.get_pressed()[key]

    def is_key_just_pressed(self, key: int):
        return key in self._keys_just_pressed

    def is_key_just_released(self, key: int):
        return key in self._keys_just_released

    def get_pressed_mouse_buttons(self):
        pressed_tuple = pg.mouse.get_pressed()
        return [i + 1 for i, val in enumerate(pressed_tuple) if val]

    def is_mouse_button_pressed(self, button: int):
        return (button - 1) < len(pg.mouse.get_pressed()) and pg.mouse.get_pressed()[
            button - 1
        ]

    def is_mouse_button_just_pressed(self, button: int):
        return (button, False) in self._mouse_buttons_just_pressed or (
            button,
            True,
        ) in self._mouse_buttons_just_pressed

    def is_mouse_button_just_released(self, button: int):
        return button in self._mouse_buttons_just_released

    def is_double_click(self, button: int):
        return ("double", button) in self._mouse_buttons_just_pressed

    def is_dragging(self, button: int):
        return self._is_dragging.get(button, False)

    def get_drag_delta(self, button: int):
        if button not in self._drag_start_pos:
            return (0, 0)
        sx, sy = self._drag_start_pos[button]
        return pg.Vector2(self._mouse_pos[0] - sx, self._mouse_pos[1] - sy)

    @property
    def mouse_pos(self):
        x, y = self._mouse_pos
        return pg.Vector2(x, y)

    @property
    def mouse_delta(self):
        x, y = self._mouse_delta
        return pg.Vector2(x, y)

    @property
    def scroll_delta(self):
        x, y = self._scroll_delta
        return pg.Vector2(x, y)
