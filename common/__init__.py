from common.network import init_packets


def init_common():
    import common.packets  # noqa: F401

    init_packets()
