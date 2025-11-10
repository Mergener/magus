from common.engine.network import init_packets


def init_common():
    import common.engine.packets  # noqa: F401

    init_packets()
