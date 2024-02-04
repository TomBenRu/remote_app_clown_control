import time

# from jnius import autoclass
# from oscpy.client import OSCClient


# PythonService = autoclass('org.kivy.android.PythonService')
# PythonService.mService.setAutoRestartService(True)

# CLIENT = OSCClient('localhost', 3002)

t = 0
while True:
    time.sleep(1)
    t += 1
    print(f'{t=}')
#     CLIENT.send_message('/message', [f'message {t}'])

