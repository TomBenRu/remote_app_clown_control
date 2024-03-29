import json
import ssl
import threading
import time

import plyer
import websocket
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
from websocket import WebSocketApp

CLIENT = OSCClient(b'localhost', 3002)
SERVER = OSCThreadServer()


class OscHandler:
    def __init__(self):
        self.client = CLIENT
        self.server = SERVER
        self.server.listen(address=b'localhost', port=3000, default=True)

        self.server.bind(b'/call', self.handle_call)
        self.server.bind(b'/connect', self.handle_connect)
        self.server.bind(b'/close_connection', self.close_connection)

        self.ws: WebSocketApp | None = None

        self.vibrator = plyer.vibrator
        self.vibrator.vibrate(time=0.2)

        self.greeting_message = None

        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> osc handler init')

    def handle_call(self, message, department_id):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> handle call {message=}, {department_id=}')
        message = message.decode('utf-8')
        if department_id:
            department_id = department_id.decode('utf-8')
        if department_id is not None and department_id == '-1':
            department_id = None
        try:
            self.ws.send(json.dumps({'chat-message': message, 'receiver_id': department_id}))
        except Exception as e:
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> handle call failed {e=}')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Message sent')

    def handle_confirmation_of_receipt(self, message):
        message_id = json.loads(message).get('message_id')
        confirmation_message = json.dumps({'message_id': message_id, 'confirmation_of_receipt': True})
        self.ws.send(confirmation_message)

    def handle_ws_message(self, ws, message):
        if json.loads(message).get('message'):
            try:
                self.vibrate()
            except Exception as e:
                print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> vibrate failed {e=}')
        self.client.send_message(b'/ws_message', [message.encode('utf-8'),])
        if (self.greeting_message and json.loads(message).get('joined') and not json.loads(message).get('reconnect')
                and (department_id := json.loads(message).get('department_id'))):
            self.handle_call(self.greeting_message, department_id.encode('utf-8'))

        self.handle_confirmation_of_receipt(message)

    def handle_ws_error(self, ws, error):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ws error {error=}')
        self.client.send_message(b'/ws_error', ['Fehler im Websocket ist aufgetreten'.encode('utf-8'),])

    def handle_ws_open(self, ws):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ws opened {ws=}')
        self.client.send_message(b'/ws_opened', ['-1'.encode('utf-8'),])

    def handle_ws_close(self, ws, close_status_code, close_msg):
        self.client.send_message(b'/ws_closed', [close_status_code.encode('utf-8'), close_msg.encode('utf-8'),])

    def handle_already_open_ws_connection(self):
        self.client.send_message(b'/ws_already_open', [1,])

    def handle_connect(self, message, ws_url, token, team_of_actors_id):
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> connect: {message=} {ws_url=}, {token=}, {team_of_actors_id=}')
        self.open_ws_connection(ws_url.decode('utf-8'),
                                token.decode('utf-8'),
                                team_of_actors_id.decode('utf-8'))
        self.greeting_message = message

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

    def close_connection(self, message):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> close connection {message=}')
            self.ws.send(json.dumps({'closing': True, 'chat-message': message.decode('utf-8')}))
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> close connection {message=} after send')
            self.ws.close()
            self.ws = None

        else:
            self.client.send_message(b'/ws_already_closed', [])

    def vibrate(self):
        self.vibrator.pattern(pattern=[0, 0.5, 0.5, 1, 0.5, 0.5, 0.5, 1])


if __name__ == '__main__':
    osc_handler = OscHandler()

    t = 0
    while True:
        time.sleep(5)
        t += 5
        print(f'>>>>>>>>>>>>>>>>>>>> {t=}')

