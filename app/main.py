import json
import ssl
import threading

import jwt
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
from kivy.metrics import sp
from kivymd.app import MDApp
from kivymd.uix.button import MDRoundFlatButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.dropdownitem import MDDropDownItem
from websocket import WebSocket, WebSocketApp

Window.softinput_mode = "below_target"


class Values:
    def __init__(self):
        self.token: str = ''
        self.user_id: str = ''
        self.session = requests.Session()
        # self.backend_url = "http://localhost:8000/"
        # self.ws_url = "ws://localhost:8000/ws/"
        self.backend_url = "https://clinic-clown-control.onrender.com/"
        self.ws_url = "wss://clinic-clown-control.onrender.com/ws/"
        self.team_of_actors = {}

    def set_session_token(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def set_user_id(self, user_id: int):
        self.user_id = user_id

    def set_team_of_actors(self, team_of_actors: dict):
        self.team_of_actors = team_of_actors


values = Values()


class LoginScreen(Screen):

    def validate_user(self):
        data = {'username': self.ids.username.text, 'password': self.ids.password.text}
        try:
            response = requests.post(f'{values.backend_url}token/', data, timeout=10)
            if response.status_code == 200 and response.json().get('status_code', 200) == 200:
                values.set_session_token(response.json().get('access_token'))
                values.set_user_id(jwt.decode(jwt=response.json().get('access_token'),
                                              options={"verify_signature": False}).get('user_id'))
                self.ids.error_label.text = ''
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'team'
            else:
                self.ids.error_label.text = 'Username oder Passwort ungültig!'
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class CreateTeamScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = MDGridLayout(cols=2, size_hint_y=None, row_force_default=True, row_default_height=98)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.users = []
        self.switches = []
        self.confirm_button = MDRoundFlatButton(text='Confirm Selection', font_size=48)
        self.confirm_button.bind(on_release=self.confirm_selection)
        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        scrollview.add_widget(self.layout)
        self.add_widget(scrollview)
        self.locations = []
        self.locations_menu_items = []

        self.location_id = None

    def on_enter(self, *args):
        self.users = self.get_users()
        for user in self.users:
            switch = MDSwitch()
            if user['id'] == values.user_id:
                switch.active = True
                switch.disabled = True
            self.switches.append(switch)
            self.layout.add_widget(Label(text=f'{user["f_name"]} {user["l_name"]}', font_size=48))
            self.layout.add_widget(switch)
        self.locations = self.get_locations()
        self.locations_menu_items = [
            {
                'viewclass': 'OneLineListItem',
                'text': location['name'],
                'font_style': 'H5',
                'on_release': (lambda loc_id=location['id'], loc_name=location['name']:
                               self.set_location_id(loc_id, loc_name))
            }
            for location in self.locations
        ]
        self.location_drop_down_item = MDDropDownItem(
            pos_hint={'center_x': .5, 'center_y': .5}, font_size=48,
            on_release=self.open_location_menu
        )
        self.location_drop_down_item.text = 'Select Location'
        self.layout.add_widget(self.location_drop_down_item)
        self.layout.add_widget(self.confirm_button)

    def open_location_menu(self, item):
        width = min(max(len(loc['name']) for loc in self.locations) * sp(15), Window.width * 0.8)
        print(width)
        self.location_menu = MDDropdownMenu(caller=item, items=self.locations_menu_items, width=width, width_mult=4)
        self.location_menu.open()

    def set_location_id(self, location_id, location_name):
        self.location_id = location_id
        self.location_drop_down_item.text = location_name
        self.location_menu.dismiss()
    def on_leave(self, *args):
        self.layout.clear_widgets()
        self.users = []
        self.switches = []
        self.location_id = None

    def on_location_spinner_text(self, instance, value):
        self.location_id = self.locations[int(self.location_spinner.text.split('.:')[0]) - 1]['id']

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
        if not self.location_id:
            return
        selected_users = [user['id'] for switch, user in zip(self.switches, self.users) if switch.active]
        try:
            response = values.session.post(f'{values.backend_url}actors/new-team',
                                           json={'location_id': self.location_id,
                                                 'actor_ids': selected_users}, timeout=10)
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

    def on_leave(self, *args):
        self.output.text = ''

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
        try:
            self.ws.send(json.dumps({"chat-message": f'{values.token}: closing'}))
            print('Closing message sent')
        except Exception as e:
            print('Fehler beim Senden: ', e)
            self.output.text += f'Problem beim Senden: {e}\n'
            return
        values.session.post(f'{values.backend_url}actors/delete-team',
                            params={'team_of_actor_id': values.team_of_actors['id']}, timeout=10)
        self.close_connection(None)
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        print(f'{threading.active_count()=}')


class ClownControllApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'BlueGray'
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeamScreen(name='team'))
        sm.add_widget(ChatScreen(name='chat'))
        return sm


if __name__ == '__main__':
    ClownControllApp().run()
