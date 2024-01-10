import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
import websocket
import ssl
import json
import threading

kivy.require('1.0.9')


class ClientApp(App):

    def build(self):
        self.ws = websocket.WebSocketApp("ws://localhost:8000/ws/notifications/",
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         header=['Cookie: ws-cookie=clown-team-token'])
        self.ws.on_open = self.on_open

        websocket.enableTrace(True)

        threading.Thread(target=self.ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}).start()

        self.layout = BoxLayout(orientation='vertical')

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

        return self.layout

    def on_message(self, ws, message):
        self.output.text += f"Received: {message}\n"

    def on_error(self, ws, error):
        self.output.text += f"Error: {error}\n"

    def on_close(self, ws, close_status_code, close_msg):
        self.output.text += f"Connection closed with status code: {close_status_code} and message: {close_msg}\n"

    def on_open(self, ws):
        self.output.text += "Connection opened\n"

    def send_message(self, instance):
        user_input = self.input.text
        data = {"message": user_input}
        json_data = json.dumps(data)
        self.ws.send(json_data)
        self.input.text = ''

    def close_connection(self, instance):
        if self.ws.sock and self.ws.sock.connected:
            self.ws.close()

if __name__ == '__main__':
    ClientApp().run()
