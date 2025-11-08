from common import init_common
from server.netserver import NetServer

if __name__ == "__main__":
    init_common()

    server = NetServer(port=16214)
    while True:
        server.poll()
