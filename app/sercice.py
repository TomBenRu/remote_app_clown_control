import time

from oscpy.client import OSCClient


CLIENT = OSCClient('localhost', 3002)

t = 0
while True:
    time.sleep(1)
    t += 1
    print("hello")
    CLIENT.send_message(b'/message', [f'message {t}'])

