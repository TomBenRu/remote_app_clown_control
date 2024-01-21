import json
import ssl
import threading

import requests
import websocket
from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label
from websocket import WebSocket, WebSocketApp

Window.softinput_mode = "below_target"


class Values:
    def __init__(self):
        self.token: str = ''
        self.session = requests.Session()
        self.backend_url = "http://localhost:8000/"
        self.ws_url = "ws://localhost:8000/ws/"
        # self.backend_url = "https://clinic-clown-control.onrender.com/"
        # self.ws_url = "wss://clinic-clown-control.onrender.com/ws/"
        self.team_of_actors = {}

    def set_session_token(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def set_team_of_actors(self, team_of_actors: dict):
        self.team_of_actors = team_of_actors


values = Values()


class LoginScreen(Screen):

    def validate_user(self):
        data = {'username': self.username.text, 'password': self.password.text}
        try:
            response = requests.post(f'{values.backend_url}token/', data, timeout=10)
            if response.status_code == 200 and response.json().get('status_code', 200) == 200:
                print(response.json())
                values.set_session_token(response.json().get('access_token'))
                self.login_error.text = ''
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'team'
            else:
                self.login_error.text = 'Username oder Passwort ungültig!'
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class CreateTeamScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = GridLayout(cols=2, size_hint_y=None, row_force_default=True, row_default_height=98)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.users = []
        self.checkboxes = []
        self.confirm_button = Button(text='Confirm Selection', font_size=48)
        self.confirm_button.bind(on_release=self.confirm_selection)
        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        scrollview.add_widget(self.layout)
        self.add_widget(scrollview)

    def on_enter(self, *args):
        self.users = self.get_users()
        for user in self.users:
            checkbox = CheckBox()
            self.checkboxes.append(checkbox)
            self.layout.add_widget(Label(text=f'{user["f_name"]} {user["l_name"]}', font_size=48))
            self.layout.add_widget(checkbox)
        self.locations = self.get_locations()
        self.location_spinner = Spinner(
            text='Select a Location',
            values=[f"{i+1}.: {l['name']}" for i, l in enumerate(self.locations)], font_size=48)
        self.layout.add_widget(self.location_spinner)
        self.layout.add_widget(self.confirm_button)

    def on_leave(self, *args):
        self.layout.clear_widgets()
        self.users = []
        self.checkboxes = []

    def get_users(self):
        try:
            response = values.session.get(f'{values.backend_url}actors/all_actors', timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException as e:
            return []

    def get_locations(self):
        try:
            response = values.session.get(f'{values.backend_url}actors/locations', timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException as e:
            return []

    def confirm_selection(self, instance):
        selected_users = [user['id'] for checkbox, user in zip(self.checkboxes, self.users) if checkbox.active]
        print(selected_users)
        try:
            location_id = self.locations[int(self.location_spinner.text.split('.:')[0]) - 1]['id']
            response = values.session.post(f'{values.backend_url}actors/new-team',
                                           json={'location_id': location_id, 'actor_ids': selected_users}, timeout=10)
            if response.status_code == 200:
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'chat'
                print([a['artist_name'] for a in response.json()['actors']])
                values.set_team_of_actors(response.json())
                print([a['artist_name'] for a in values.team_of_actors['actors']])
            else:
                self.layout.add_widget(Label(text='Fehler bei der Teamerstellung!'))
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ws: WebSocketApp | None = None
        self.layout = GridLayout(cols=2, size_hint_y=None)

    def open_connection(self):
        if self.ws:
            self.output.text += f"Connection already open!\n"
            return
        self.ws = websocket.WebSocketApp(values.ws_url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         cookie=f'clown-call-auth={values.token}',
                                         header={'team_of_actors_id': values.team_of_actors['id']})
        self.ws.on_open = self.on_open
        threading.Thread(target=self.ws.run_forever,
                         kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}, 'reconnect': 5}).start()

    @mainthread
    def on_message(self, ws, message):
        self.output.text += f"{message}\n"

    @mainthread
    def on_error(self, ws: WebSocket, error):
        print(f'{error=}')
        self.output.text += f"Error: {error}\n"
        self.close_connection(None)

    @mainthread
    def on_close(self, ws, close_status_code, close_msg):
        self.output.text += f"Connection closed with status code: {close_status_code} and message: {close_msg}\n"

    @mainthread
    def on_open(self, ws):
        print("Websocket connection opened")
        self.output.text += "Connection opened\n"

    @mainthread
    def send_message(self):
        user_input = self.input.text
        data = {"chat-message": user_input}
        json_data = json.dumps(data)
        try:
            self.ws.send(json_data)
        except Exception as e:
            self.output.text += f'Problem beim Senden: {e}\n'
            return
        self.input.text = ''

    @mainthread
    def close_connection(self, instance):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.close()
            self.ws = None
        else:
            self.output.text += "Not connected\n"

    def logout(self):
        values.session.post(f'{values.backend_url}actors/delete-team',
                            params={'team_of_actor_id': values.team_of_actors['id']}, timeout=10)
        self.close_connection(None)
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        print(f'{threading.active_count()=}')


class ClownControllApp(App):
    def build(self):
        Window.clearcolor = (0.2, 0.2, 0.2, 1)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeamScreen(name='team'))
        sm.add_widget(ChatScreen(name='chat'))
        return sm


if __name__ == '__main__':
    ClownControllApp().run()
