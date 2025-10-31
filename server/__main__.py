from server.netserver import NetServer

if __name__ == "__main__":
    server = NetServer(port=9999)
    while True:
        server.poll()