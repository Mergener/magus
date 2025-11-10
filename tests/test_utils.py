from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.engine.utils import overrides_method


class CustomBehaviour(Behaviour):
    def on_update(self, dt):
        print("I implement update!")


def test_overrides_method():
    cb = CustomBehaviour(Node())

    assert overrides_method(Behaviour, cb, "on_update")
    assert not overrides_method(Behaviour, cb, "on_tick")
    assert not overrides_method(Behaviour, cb, "on_render")
