from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

if TYPE_CHECKING:
    from common.behaviour import Behaviour
    from common.game import Game
    from common.transform import Transform


class Node:
    def __init__(self, game: Game | None = None):
        from common.transform import Transform

        self._children: list[Self] = []
        self._parent: Self | None = None
        self._behaviours: list[Behaviour] = []
        self._game = game
        self.add_behaviour(Transform)

    @property
    def game(self) -> Game | None:
        return self._game

    def bind_to_game(self, game: Game):
        if self._game == game:
            return

        self._game = game
        for b in self._behaviours:
            # Setting properties force behaviours to subscribe to
            # proper simulation events.
            b.visible = b.visible
            b.receive_updates = b.receive_updates

        for c in self._children:
            c.bind_to_game(game)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent: Self | None):
        if self._parent is not None:
            self._parent._children.remove(self)

        self._parent = parent

        if parent:
            parent._children.append(self)
            if self._game != parent._game:
                self._game = parent._game
                for b in self._behaviours:
                    b.visible = b.visible
                    b.receive_updates = b.receive_updates

    def add_child(self, child: Self | None):
        if child is None:
            child = self.__class__(self._game)
        child.parent = self
        return child

    def remove_child(self, child: Self):
        if child.parent == self:
            child.parent = None

    def get_behaviour[T: Behaviour](self, t: type[T]) -> T | None:
        for b in self._behaviours:
            if isinstance(b, t):
                return b
        return None

    def add_behaviour[T: Behaviour](self, tb: type[T]) -> T:
        b = tb(self)
        self._behaviours.append(b)
        return b

    @property
    def transform(self) -> Transform:
        return cast(Transform, self._behaviours[0])

    def destroy(self):
        if self._game is None:
            return

        self.parent = None
        self._destroy_helper()

    def _destroy_helper(self):
        for b in self._behaviours:
            b.visible = False
            b.receive_updates = False
            b.on_destroy()

        self._behaviours.clear()

        for c in self._children:
            c._destroy_helper()

        self._children.clear()
        if self._game is not None:
            self._game = None
