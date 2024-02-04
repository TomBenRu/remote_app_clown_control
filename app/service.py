import time

# from jnius import autoclass
from oscpy.client import OSCClient


# PythonService = autoclass('org.kivy.android.PythonService')
# PythonService.mService.setAutoRestartService(True)

CLIENT = OSCClient('localhost', 3002)

if __name__ == '__main__':

    t = 0
    while True:
        time.sleep(1)
        t += 1
        print(f'{t=}')
        message = f'message {t}'.encode('utf-8')
        try:
            CLIENT.send_message(b'/message', [message,],)
        except Exception as e:
            print(f'------------------Fehler: {e}---------------------------')

