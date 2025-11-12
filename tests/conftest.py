import pytest

from common.engine.network import auto_resolve_packets


@pytest.fixture(autouse=True)
def startup():
    auto_resolve_packets()
