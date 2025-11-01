import pytest
from common import init_common

@pytest.fixture(autouse=True)
def startup():
    init_common()