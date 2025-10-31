from client.netclient import NetClient
from common import init_common
from common.enums import DeliveryMode

if __name__ == "__main__":
    init_common()
    
    client = NetClient("localhost", 9999)
    while True:
        client.send(input().encode(), DeliveryMode.RELIABLE)
        for msg in client.poll():
            print("Received:", msg)