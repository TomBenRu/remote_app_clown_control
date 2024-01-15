import time

import kivy
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
import websocket
from websocket import WebSocketApp, WebSocket
from websocket._exceptions import WebSocketConnectionClosedException
import ssl
import json
import threading

kivy.require('1.0.9')


class ClientApp(App):

    def build(self):
        websocket.enableTrace(True)

        self.ws = None

        self.layout = BoxLayout(orientation='vertical')

        self.login_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        self.input_username = TextInput(multiline=False)
        self.input_password = TextInput(multiline=False, password=True)
        self.login_layout.add_widget(self.input_username)
        self.login_layout.add_widget(self.input_password)
        self.login_button = Button(text="Login")
        self.login_button.bind(on_press=self.login)
        self.login_layout.add_widget(self.login_button)
        self.layout.add_widget(self.login_layout)

        self.output = Label(size_hint_y=0.8)
        self.layout.add_widget(self.output)

        self.input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)

        self.input = TextInput(multiline=False)
        self.input.bind(on_text_validate=self.send_message)
        self.input_layout.add_widget(self.input)

        self.send_button = Button(text="Send")
        self.send_button.bind(on_press=self.send_message)
        self.input_layout.add_widget(self.send_button)

        self.layout.add_widget(self.input_layout)

        self.close_button = Button(text="Close Connection", size_hint_y=0.1)
        self.close_button.bind(on_press=self.close_connection)
        self.layout.add_widget(self.close_button)

        # if local: "ws://localhost:8000/ws/", else render: "wss://clinic-clown-control.onrender.com/ws/"
        self.local = False
        if self.local:
            self.backend_url = "http://localhost:8000/"
            self.ws_url = "ws://localhost:8000/ws/"
        else:
            self.backend_url = "https://clinic-clown-control.onrender.com/"
            self.ws_url = "wss://clinic-clown-control.onrender.com/ws/"

        return self.layout

    def on_message(self, ws, message):
        self.output.text += f"{message}\n"

    def on_error(self, ws: WebSocket, error):
        print(f'{error=}')
        self.output.text += f"Error: {error}\n"

    def on_close(self, ws, close_status_code, close_msg):
        self.output.text += f"Connection closed with status code: {close_status_code} and message: {close_msg}\n"

    def on_open(self, ws):
        self.output.text += "Connection opened\n"

    def send_message(self, instance):
        user_input = self.input.text
        data = {"chat-message": user_input}
        json_data = json.dumps(data)
        try:
            self.ws.send(json_data)
        except Exception as e:
            self.output.text += f'Problem beim Senden: {e}\n'
            return
        self.input.text = ''

    def login(self, instance):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.output.text += "Already connected\n"
            return
        username = self.input_username.text
        password = self.input_password.text
        data = {"username": username, "password": password}
        try:
            response = requests.post(f'{self.backend_url}token/', data, timeout=10)
        except requests.exceptions.Timeout:
            self.output.text += "Login failed: Timeout\n"
            return

        if response.status_code == 200 and response.json().get('status_code') != 409:
            print(f'{response.status_code}: {response.json()}')
            print('success:', response.json())
            self.output.text += "Login successful\n"
            print('token:', response.json()['access_token'])
            self.open_connection(response.json()['access_token'])
        else:
            print(f'failed: {response.json()}')
            self.output.text += f"Login failed with status code {response.status_code}\n"

    def open_connection(self, token: str):
        self.ws = websocket.WebSocketApp(self.ws_url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         cookie=f'clown-call-auth={token}')
        self.ws.on_open = self.on_open
        threading.Thread(target=self.ws.run_forever,
                         kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}, 'reconnect': 5}).start()

    def close_connection(self, instance):
        if self.ws.sock and self.ws.sock.connected:
            self.ws.close()


if __name__ == '__main__':
    ClientApp().run()
