from common.simulation import Behaviour
from common.utils import overrides_method


class CustomBehaviour(Behaviour):
    def __init__(self):
        super().__init__()

    def on_update(self, dt):
        print("I implement update!")


def test_overrides_method():
    cb = CustomBehaviour()

    assert overrides_method(Behaviour, cb, "on_update")
    assert not overrides_method(Behaviour, cb, "on_tick")
    assert not overrides_method(Behaviour, cb, "on_render")
