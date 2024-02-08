import json
import pickle
import ssl
import threading
import time

import websocket
# from jnius import autoclass
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
from websocket import WebSocketApp

# PythonService = autoclass('org.kivy.android.PythonService')
# PythonService.mService.setAutoRestartService(True)

CLIENT = OSCClient(b'localhost', 3002)
SERVER = OSCThreadServer()


def handle_call(chat_message, department_id):
    chat_message = chat_message.decode('utf-8')
    department_id = department_id.decode('utf-8')
    print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> call: {chat_message=}, {department_id=}')


class OscHandler:
    def __init__(self):
        self.client = CLIENT
        self.server = SERVER
        self.server.listen(address=b'localhost', port=3000, default=True)

        self.server.bind(b'/call', self.handle_call)
        self.server.bind(b'/connect', self.handle_connect)

        self.ws: WebSocketApp | None = None
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> osc handler init')

    def handle_call(self, call):
        ...

    def handle_ws_message(self, ws, message):
        self.client.send_message(b'/ws_message', [message.encode('utf-8'),])

    def handle_ws_error(self, ws, error):
        self.client.send_message(b'/ws_error', [error.encode('utf-8'),])

    def handle_ws_open(self, ws):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ws opened {ws=}')
        ws_pickled = pickle.dumps(ws)
        self.client.send_message(b'/ws_opened', [ws_pickled])

    def handle_ws_close(self, ws, close_status_code, close_msg):
        self.client.send_message(b'/ws_closed', [close_status_code.encode('utf-8'), close_msg.encode('utf-8'),])

    def handle_already_open_ws_connection(self):
        self.client.send_message(b'/ws_already_open', [1,])

    def handle_connect(self, ws_url, token, team_of_actors_id):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> connect: {ws_url=}, {token=}, {team_of_actors_id=}')
        self.open_ws_connection(ws_url.decode('utf-8'),
                                token.decode('utf-8'),
                                team_of_actors_id.decode('utf-8'))

    def open_ws_connection(self, ws_url: str, token: str, team_of_actors_id: str):
        if self.ws:
            self.handle_already_open_ws_connection()
            return
        self.ws = websocket.WebSocketApp(ws_url,
                                         on_message=self.handle_ws_message,
                                         on_error=self.handle_ws_error,
                                         on_close=self.handle_ws_close,
                                         cookie=f'clown-call-auth={token}',
                                         header={'team_of_actors_id': team_of_actors_id})
        self.ws.on_open = self.handle_ws_open
        threading.Thread(target=self.ws.run_forever,
                         kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}, 'reconnect': 5}).start()


if __name__ == '__main__':
    # SERVER.listen(b'localhost', port=3000, default=True)
    # SERVER.bind(b'/call', handle_call)
    osc_handler = OscHandler()

    t = 0
    while True:
        time.sleep(10)
        t += 1
        print(f'>>>>>>>>>>>>>>>>>>>> {t=}')
        # message = f'message {t}'.encode('utf-8')
        # try:
        #     CLIENT.send_message(b'/message', [message,],)
        # except Exception as e:
        #     print(f'------------------Fehler: {e}---------------------------')

