from __future__ import annotations

import importlib
import traceback
from typing import TYPE_CHECKING, Self, cast

if TYPE_CHECKING:
    from common.behaviour import Behaviour
    from common.behaviours.transform import Transform
    from common.game import Game


class Node:
    def __init__(self, game: Game | None = None, name: str | None = None):
        from common.behaviours.transform import Transform

        self._name = name
        self._children: list[Self] = []
        self._parent: Self | None = None
        self._behaviours: list[Behaviour] = []
        self._destroyed = False
        self._game = game
        self.add_behaviour(Transform)
        self.skip_serialization = False

    @property
    def game(self) -> Game | None:
        return self._game

    @property
    def name(self):
        return self._name or "<unnamed>"

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

    def get_child(self, idx: int):
        return self._children[idx]

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

    def get_or_add_behaviour[T: Behaviour](self, tb: type[T]) -> T:
        b = self.get_behaviour(tb)
        if b is not None:
            return b
        return self.add_behaviour(tb)

    @property
    def transform(self) -> Transform:
        from common.behaviours.transform import Transform

        return cast(Transform, self._behaviours[0])

    def destroy(self):
        if self._destroyed or self._game is None:
            return

        self._destroyed = True
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

        if self._name is not None:
            out_dict["name"] = self._name

        children = []
        for c in self.children:
            cd: dict = {}
            if c.skip_serialization:
                continue

            c.serialize(cd)
            children.append(cd)
        out_dict["children"] = children

        behaviours = []
        for b in self._behaviours:
            if b.skip_serialization:
                continue

            bd = {
                "__type": _get_behaviour_type_name(b),
                "receive_updates": b.receive_updates,
                "visible": b.visible,
            }

            b.on_serialize(bd)
            behaviours.append(bd)
        out_dict["behaviours"] = behaviours

        return out_dict

    def deserialize(self, in_dict: dict):
        from common.assets import load_node_asset
        from common.behaviours.transform import Transform

        self._name = in_dict.get("name")

        dict_children = in_dict.get("children", [])
        dict_behaviours = in_dict.get("behaviours", [])
        for dc in dict_children:
            if isinstance(dc, dict):
                node = Node(self.game)
                node.parent = self
                node.deserialize(dc)
            elif isinstance(dc, str):
                node = load_node_asset(dc)
                node.parent = self

        for db in dict_behaviours:
            behaviour_type = _get_behaviour_type_by_name(db.get("__type"))
            if behaviour_type is None:
                continue

            if behaviour_type is not Transform:
                b = self.add_behaviour(behaviour_type)
            else:
                b = self.get_behaviour(Transform)
                if b is None:
                    b = self.add_behaviour(Transform)

            b.on_deserialize(db)
            b.receive_updates = db.get("receive_updates", True)
            b.visible = db.get("visible", True)

        self._ensure_transform_is_first_behaviour()

        return self

    def _ensure_transform_is_first_behaviour(self):
        from common.behaviours.transform import Transform

        if len(self._behaviours) > 0 and isinstance(self._behaviours[0], Transform):
            return

        existing_idx = -1
        for i in range(1, len(self._behaviours)):
            if isinstance(self._behaviours[i], Transform):
                existing_idx = i
                break

        if existing_idx == -1:
            transform = self.add_behaviour(Transform)
        else:
            transform = cast(Transform, self._behaviours[existing_idx])
            del self._behaviours[existing_idx]

        self._behaviours.insert(0, transform)

    def clone(self):
        # TODO: Improve performance
        data = self.serialize()
        new_node = Node(self._game)
        new_node.deserialize(data)
        return new_node

    def find_behaviour_in_children[T: Behaviour](
        self, tb: type[T], include_self: bool = True, recursive: bool = False
    ) -> T | None:
        if include_self:
            b = self.get_behaviour(tb)
            if b:
                return b

        for c in self._children:
            b = c.get_behaviour(tb)
            if b:
                return b

        if recursive:
            for c in self._children:
                b = c.find_behaviour_in_children(tb, include_self=False, recursive=True)
                if b:
                    return b

        return None

    def find_behaviours_in_children[T: Behaviour](
        self,
        tb: type[T],
        include_self: bool = True,
        recursive: bool = False,
        behaviour_list: list[T] | None = None,
    ) -> list[T]:
        if behaviour_list is None:
            behaviour_list = []

        if include_self:
            b = self.get_behaviour(tb)
            if b:
                behaviour_list.append(b)

        for c in self._children:
            b = c.get_behaviour(tb)
            if b:
                behaviour_list.append(b)

        if recursive:
            for c in self._children:
                c.find_behaviours_in_children(
                    tb,
                    include_self=False,
                    recursive=True,
                    behaviour_list=behaviour_list,
                )

        return behaviour_list


_behaviour_types: dict[str, type[Behaviour]] | None = None


def _get_behaviour_type_name(b: Behaviour | type[Behaviour]):
    from common.behaviour import Behaviour

    if isinstance(b, Behaviour):
        b = b.__class__
    return f"{b.__module__}.{b.__name__}"


def _get_behaviour_type_by_name(name: str | None):
    global _behaviour_types

    if name is None:
        return None

    if _behaviour_types is None:
        _behaviour_types = {}
        from common.behaviour import Behaviour

        _import_behaviour_types_from_superclass(Behaviour)

    bt = _behaviour_types.get(name)
    if bt is not None:
        return bt

    try:
        module_name, class_name = name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        bt = getattr(module, class_name)
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Failed to import module {module_name}: {trace}")
        return None

    _behaviour_types[name] = bt
    return bt


def _import_behaviour_types_from_superclass(cls: type[Behaviour]):
    global _behaviour_types
    assert _behaviour_types is not None

    for bt in cls.__subclasses__():
        _behaviour_types[_get_behaviour_type_name(bt)] = bt
        _import_behaviour_types_from_superclass(bt)
