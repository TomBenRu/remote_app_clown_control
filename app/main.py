import json
import threading

import jwt
import plyer
import requests
from jnius import autoclass
from kivy import platform
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import sp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.tab import MDTabsBase
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
from websocket import WebSocket, WebSocketApp


Window.softinput_mode = "below_target"

SERVICE_NAME = 'Websocket'
NOTIFICATION_SERVICE_NAME = 'Notification'


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
        self.departments_of_location = {}
        self.mActivity = None
        self.service = None
        self.notification_service = None

    def set_session_token(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def set_user_id(self, user_id: int):
        self.user_id = user_id

    def set_team_of_actors(self, team_of_actors: dict):
        self.team_of_actors = team_of_actors

    def set_departments_of_location(self, departments_of_location: list[dict]):
        self.departments_of_location = {d['id']: d for d in departments_of_location}
        print(self.departments_of_location)


values = Values()


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('../racc.json')
        if self.store.exists('login_data'):
            self.ids.username.text = self.store.get('login_data')['username']
            self.ids.password.text = self.store.get('login_data')['password']

    def validate_user(self):
        data = {'username': self.ids.username.text, 'password': self.ids.password.text}
        try:
            response = requests.post(f'{values.backend_url}token/', data, timeout=10)
            if response.status_code == 200 and response.json().get('status_code', 200) == 200:
                values.set_session_token(response.json().get('access_token'))
                values.set_user_id(jwt.decode(jwt=response.json().get('access_token'),
                                              options={"verify_signature": False}).get('user_id'))
                self.store.put('login_data', username=self.ids.username.text, password=self.ids.password.text)
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

        self.users = []
        self.checkboxes = []
        self.locations = []
        self.locations_menu_items = []

        self.location_id = None

    def on_enter(self, *args):
        self.users = self.get_users()
        for user in self.users:
            layout = MDBoxLayout(orientation='horizontal')
            checkbox = MDCheckbox(size_hint=(None, None), size=(60, 50))
            if user['id'] == values.user_id:
                checkbox.active = True
                # checkbox.disabled = True
            self.checkboxes.append(checkbox)
            label = MDLabel(text=f'{user["f_name"]} {user["l_name"]}', font_style='H6')
            layout.add_widget(label)
            layout.add_widget(checkbox)
            self.ids.layout_clowns_select.add_widget(layout)
        self.locations = self.get_locations()
        self.locations_menu_items = [
            {
                'viewclass': 'OneLineListItem',
                'text': location['name'],
                'font_style': 'H6',
                'on_release': (lambda loc_id=location['id'], loc_name=location['name']:
                               self.set_location_id(loc_id, loc_name))
            }
            for location in self.locations
        ]

    def open_location_menu(self, item):
        width = min(max(len(loc['name']) for loc in self.locations) * sp(15), Window.width * 0.8)
        print(width)
        self.location_menu = MDDropdownMenu(caller=item, items=self.locations_menu_items, width=width, width_mult=4)
        self.location_menu.open()

    def set_location_id(self, location_id, location_name):
        self.location_id = location_id
        self.ids.dropdown_locations.text = location_name
        self.location_menu.dismiss()
    def on_leave(self, *args):
        self.ids.layout_clowns_select.clear_widgets()
        self.ids.dropdown_locations.text = 'Select Location'
        self.users = []
        self.checkboxes = []
        self.location_id = None

    def get_users(self):
        try:
            response = values.session.get(f'{values.backend_url}actors/all_available_actors', timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException as e:
            return []

    def get_locations(self):
        try:
            response = values.session.get(f'{values.backend_url}actors/locations', timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException as e:
            return []

    def create_team(self):
        if not self.location_id:
            return
        selected_users = [user['id'] for switch, user in zip(self.checkboxes, self.users) if switch.active]
        try:
            response = values.session.post(f'{values.backend_url}actors/new-team',
                                           json={'location_id': self.location_id,
                                                 'actor_ids': selected_users}, timeout=10)
            if response.status_code == 200:
                response_departments = values.session.get(f'{values.backend_url}actors/departments_of_location',
                                                          params={'location_id': self.location_id}, timeout=10)
                print(f'{response_departments.json()=}')
                if response_departments.status_code == 200:
                    values.set_departments_of_location(response_departments.json())
                else:
                    values.session.post(f'{values.backend_url}actors/delete-team',
                                        params={'team_of_actor_id': values.team_of_actors['id']}, timeout=10)
                    self.layout_clown_select.add_widget(Label(text='Fehler beim Abruf der Abteilungen!'))
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'chat'
                print([a['artist_name'] for a in response.json()['actors']])
                values.set_team_of_actors(response.json())
                print([a['artist_name'] for a in values.team_of_actors['actors']])
            else:
                self.layout_clown_select.add_widget(Label(text='Fehler bei der Teamerstellung!'))
        except requests.exceptions.RequestException as e:
            self.layout_clown_select.add_widget(Label(text=str(e)))


class ChatTab(FloatLayout, MDTabsBase):
    def __init__(self, osc_client: OSCClient, notification_client: OSCClient, tab_pos: int, department_id=None, **kwargs):
        super().__init__(**kwargs)
        self.tab_pos = tab_pos
        self.department_id = department_id
        self.client = osc_client
        self.notification_client = notification_client
        self.layout = GridLayout(cols=2, size_hint_y=None)

    @mainthread
    def send_message(self):
        user_input = self.ids.input.text
        self.client.send_message(b'/call',
                                 [user_input.encode('utf-8'),
                                  self.department_id.encode('utf-8') if self.department_id else '-1'.encode('utf-8')])
        self.notification_client.send_message(b'/notify', [])
        self.ids.input.text = ''


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog_exit = None
        self.ws: WebSocketApp | None = None
        self.chat_tabs: dict[str, ChatTab] = {}
        self.client = OSCClient(b'localhost', 3000)
        self.notification_client = OSCClient(b'localhost', 3004)
        self.server = server = OSCThreadServer()
        server.listen(
            address=b'localhost',
            port=3002,
            default=True,
        )
        server.bind(b'/ws_message', self.on_message)
        server.bind(b'/ws_opened', self.ws_opened)

    @mainthread
    def ws_opened(self, department_id):
        print(f'{department_id=}')
        new_chat_tab = ChatTab(tab_label_text='Chat', osc_client=self.client, notification_client=self.notification_client, tab_pos=0)
        self.chat_tabs['common_chat'] = new_chat_tab
        self.ids.chat_tabs.add_widget(new_chat_tab)

    def on_tab_switch(self, *args):
        print(args)

    def create_connection_service(self):
        self.client.send_message(b'/connect',
                                 [values.ws_url.encode('utf-8'),
                                        values.token.encode('utf-8'),
                                        values.team_of_actors['id'].encode('utf-8')])

    @mainthread
    def on_message(self, message):
        message_dict = json.loads(message.decode('utf-8'))
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>>> {message_dict=}')
        send_confirmation = message_dict.get('send_confirmation')
        receiver_id = message_dict.get('receiver_id')
        department_id = message_dict.get('department_id')
        clowns_team_id = message_dict.get('clowns_team_id')
        message = message_dict.get('message')
        joined = message_dict.get('joined')
        left = message_dict.get('left')

        if send_confirmation:
            if not receiver_id:
                for chat_tab in self.chat_tabs.values():
                    chat_tab.ids.output.text += f">>> {send_confirmation}\n"
            else:
                self.chat_tabs[receiver_id].ids.output.text += f">>> {send_confirmation}\n"
                self.chat_tabs['common_chat'].ids.output.text += f">>> {values.departments_of_location[receiver_id]['name']}: {send_confirmation}\n"
        elif message:
            if department_id:
                self.chat_tabs['common_chat'].ids.output.text += (f"<<< {values.departments_of_location[department_id]['name']}:"
                                                                  f" {message}\n")
                self.chat_tabs[department_id].ids.output.text += f"<<< {message}\n"
            else:
                ...
        elif joined:
            if department_id and not self.chat_tabs.get(department_id):
                self.chat_tabs['common_chat'].ids.output.text += (f"{values.departments_of_location[department_id]['name']}"
                                                                  f" hat den Chat betreten.\n")
                new_chat_tab = ChatTab(tab_label_text=f'{values.departments_of_location[department_id]["name"]}',
                                       department_id=department_id, osc_client=self.client, notification_client=self.notification_client, tab_pos=len(self.chat_tabs))
                self.chat_tabs[department_id] = new_chat_tab
                self.ids.chat_tabs.add_widget(new_chat_tab)
            else:
                ...
        elif left:
            if department_id:
                self.chat_tabs['common_chat'].ids.output.text += (f"{values.departments_of_location[department_id]['name']}"
                                                                  f" hat den Chat verlassen.\n")
                self.ids.chat_tabs.remove_widget(self.ids.chat_tabs.get_tab_list()[self.chat_tabs[department_id].tab_pos])
                del self.chat_tabs[department_id]
            else:
                ...

    @mainthread
    def on_error(self, ws: WebSocket, error):
        print(f'{error=}')

    @mainthread
    def on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed with status code: {close_status_code} and message: {close_msg}")
        # self.output.text += f"Connection closed with status code: {close_status_code} and message: {close_msg}\n"

    @mainthread
    def on_open(self, ws):
        print("Websocket connection opened")
        # self.output.text += "Connection opened\n"

    def ask_for_logout(self):
        if not self.dialog_exit:
            self.dialog_exit = MDDialog(
                title='Logout', text='Wollen Sie sich wirklich ausloggen\nund die Anwendung beenden?',
                buttons=[
                    MDFlatButton(text='Ja', on_release=self.logout),
                    MDFlatButton(text='Nein', on_release=self.close_dialog_exit)
                ]
            )
        self.dialog_exit.open()

    def close_dialog_exit(self, instance):
        self.dialog_exit.dismiss(force=True)

    def logout(self, instance):
        self.client.send_message(b'/call',
                                 ['Wir verabschieden uns für heute. Danke für die Unterstützung!'.encode('utf-8'),
                                  '-1'.encode('utf-8')])
        values.session.post(f'{values.backend_url}actors/delete-team',
                            params={'team_of_actor_id': values.team_of_actors['id']}, timeout=10)
        self.client.send_message(b'/close_connection', [])
        if platform == 'android' and values.service:
            values.service.stop(values.mActivity)

        for tab in self.ids.chat_tabs.get_tab_list():
            print(f'{tab=}')
            self.ids.chat_tabs.remove_widget(tab)

        self.chat_tabs = {}

        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        print(f'{threading.active_count()=}')
        MDApp.get_running_app().stop()


class ClownControlApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Orange'
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeamScreen(name='team'))
        sm.add_widget(ChatScreen(name='chat'))
        return sm

    def start_service(self):
        from android import mActivity
        context = mActivity.getApplicationContext()
        service_name = f'{str(context.getPackageName())}.Service{SERVICE_NAME}'
        print(f'SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS {service_name=}')
        service = autoclass(service_name)
        values.mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(values.mActivity, argument)
        values.service = service

    def start_notification_service(self):
        from android import mActivity
        context = mActivity.getApplicationContext()
        service_name = f'{str(context.getPackageName())}.Service{NOTIFICATION_SERVICE_NAME}'
        service = autoclass(service_name)
        values.mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(values.mActivity, argument)
        values.notification_service = service

    def on_start(self):
        if platform == 'android':
            self.start_service()
            # self.start_notification_service()


if __name__ == '__main__':
    ClownControlApp().run()
