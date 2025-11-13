from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

if TYPE_CHECKING:
    from common.engine.behaviour import Behaviour
    from common.engine.game import Game
    from common.engine.transform import Transform


class Node:
    def __init__(self, game: Game | None = None):
        from common.engine.transform import Transform

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

        for c in self._children:
            c.bind_to_game(game)

        self._game = game
        for b in self._behaviours:
            b.visible = b.visible
            b.receive_updates = b.receive_updates

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent: Self | None):
        if self._parent is not None:
            self._parent._children.remove(self)

        self._parent = parent

        if parent is None:
            return

        parent._children.append(self)
        if self._game != parent.game and parent.game is not None:
            self.bind_to_game(parent.game)

    def add_child(self, child: Self | None = None):
        if child is None:
            child = self.__class__(self._game)
        child.parent = self
        return child

    def remove_child(self, child: Self):
        if child.parent == self:
            child.parent = None

    @property
    def children(self):
        return iter(self._children)

    @property
    def behaviours(self):
        return iter(self._behaviours)

    def get_behaviour[T: Behaviour](self, t: type[T]) -> T | None:
        for b in self._behaviours:
            if isinstance(b, t):
                return b
        return None

    def add_behaviour[T: Behaviour](self, tb: type[T]) -> T:
        b = tb(self)
        self._behaviours.append(b)
        b.visible = b.visible
        b.receive_updates = b.receive_updates
        return b

    @property
    def transform(self) -> Transform:
        from common.engine.transform import Transform

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

    def serialize(self, out_dict: dict | None = None) -> dict:
        if out_dict is None:
            out_dict = {}

        children = []
        for c in self.children:
            cd: dict = {}
            c.serialize(cd)
            children.append(cd)
        out_dict["children"] = children

        behaviours = []
        for b in self._behaviours:
            bd = {"__type": _get_behaviour_type_name(b)}
            b.on_serialize(bd)
            behaviours.append(bd)
        out_dict["behaviours"] = behaviours

        return out_dict

    def deserialize(self, in_dict: dict):
        dict_children = in_dict.get("children", [])
        dict_behaviours = in_dict.get("behaviours", [])
        for dc in dict_children:
            node = Node(self.game)
            node.parent = self
            node.deserialize(dc)

        for db in dict_behaviours:
            behaviour_type = _get_behaviour_type_by_name(db.get("__type"))
            if behaviour_type is None:
                continue

            b = self.add_behaviour(behaviour_type)
            b.on_deserialize(db)

        return self


_behaviour_types: dict[str, type[Behaviour]] | None = None


def _get_behaviour_type_name(b: Behaviour | type[Behaviour]):
    from common.engine.behaviour import Behaviour

    if isinstance(b, Behaviour):
        b = b.__class__
    return f"{b.__module__}.{b.__name__}"


def _get_behaviour_type_by_name(name: str | None):
    from common.engine.behaviour import Behaviour

    global _behaviour_types

    if name is None:
        return None

    if _behaviour_types is None:
        _behaviour_types = {}
        _import_behaviour_types_from_superclass(Behaviour)
    return _behaviour_types[name]


def _import_behaviour_types_from_superclass(cls: type[Behaviour]):
    global _behaviour_types
    assert _behaviour_types is not None

    for bt in cls.__subclasses__():
        _behaviour_types[_get_behaviour_type_name(bt)] = bt
        _import_behaviour_types_from_superclass(bt)
