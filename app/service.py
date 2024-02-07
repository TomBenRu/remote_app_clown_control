import json
import time

# from jnius import autoclass
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer

# PythonService = autoclass('org.kivy.android.PythonService')
# PythonService.mService.setAutoRestartService(True)

CLIENT = OSCClient(b'localhost', 3002)
SERVER = OSCThreadServer()


def handle_call(call):
    call = json.loads(call.decode('utf-8'))
    print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> call: {call}')


if __name__ == '__main__':
    SERVER.listen(b'localhost', port=3000, default=True)
    SERVER.bind(b'/call', handle_call)

    t = 0
    while True:
        time.sleep(10)
        t += 1
        print(f'{t=}')
        message = f'message {t}'.encode('utf-8')
        try:
            CLIENT.send_message(b'/message', [message,],)
        except Exception as e:
            print(f'------------------Fehler: {e}---------------------------')

