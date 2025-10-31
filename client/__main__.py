from client.netclient import NetClient
from common.enums import DeliveryMode

def run():
    client = NetClient("localhost", 9999)
    while True:
        client.send(input().encode(), DeliveryMode.RELIABLE)
        for msg in client.poll():
            print("Received:", msg)

if __name__ == "__main__":
    run()