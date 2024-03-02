import json
import threading
from collections import defaultdict
from typing import Literal

import jwt
import plyer
import requests
from jnius import autoclass
from kivy import platform
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
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
        self.store: JsonStore = JsonStore('../racc.json')
        self.connect_to_past_ws = False

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
        if values.store.exists('login_data'):
            self.ids.username.text = values.store.get('login_data')['username']
            self.ids.password.text = values.store.get('login_data')['password']
        self.info_dlg: MDDialog | None = None

    def validate_user(self, *args):
        if self.info_dlg:
            self.info_dlg.dismiss()
        data = {'username': self.ids.username.text, 'password': self.ids.password.text}
        try:
            response = requests.post(f'{values.backend_url}token/', data, timeout=10)
            if response.status_code == 200 and response.json().get('status_code', 200) == 200:
                values.set_session_token(response.json().get('access_token'))
                values.set_user_id(jwt.decode(jwt=response.json().get('access_token'),
                                              options={"verify_signature": False}).get('user_id'))
                values.store.put('login_data', username=self.ids.username.text, password=self.ids.password.text)
                self.ids.error_label.text = ''
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'team'
            else:
                self.ids.error_label.text = 'Username oder Passwort ungültig!'
        except requests.exceptions.RequestException as e:
            self.info_dlg = MDDialog(title='Verbindungsfehler',
                                text='Es konnte keine Verbindung zum Server hergestellt werden.',
                                buttons=[MDFlatButton(text="Try again", on_release=self.validate_user),
                                         MDFlatButton(text="Cancel", on_release=self.dismiss)])
            self.info_dlg.open()

    def dismiss(self, *args):
        self.info_dlg.dismiss()
        values.service.stop(values.mActivity)
        MDApp.get_running_app().stop()


class CreateTeamScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.users = []
        self.checkboxes = []
        self.locations = []
        self.locations_menu_items = []

        self.location_id = None

    def on_enter(self, *args):
        if values.store.exists('team_of_actors') and values.store.get('team_of_actors')['id']:
            print(f'............................ Team of actors found {values.store.get("team_of_actors")["id"]=}')

            if team_of_actors := self.get_team_from_server(values.store.get('team_of_actors')['id']):
                values.set_team_of_actors(team_of_actors)
                values.connect_to_past_ws = True
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'chat'
                self.get_departments_from_server(values.team_of_actors['location']['id'])
                return

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

    def get_team_from_server(self, team_id):
        response_departments = values.session.get(f'{values.backend_url}actors/team_of_actors',
                                                  params={'team_of_actors_id': team_id}, timeout=10)
        if response_departments.status_code == 200:
            return response_departments.json()
        else:
            return None

    def get_departments_from_server(self, location_id):
        response_departments = values.session.get(f'{values.backend_url}actors/departments_of_location',
                                                  params={'location_id': location_id}, timeout=10)
        print(f'{response_departments.json()=}')
        if response_departments.status_code == 200:
            values.set_departments_of_location(response_departments.json())
        else:
            values.session.delete(f'{values.backend_url}actors/delete-team',
                                  params={'team_of_actor_id': values.team_of_actors['id']}, timeout=10)
            self.layout_clown_select.add_widget(Label(text='Fehler beim Abruf der Abteilungen!'))

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
        selected_users = [user['id'] for switch, user in zip(self.checkboxes, self.users) if switch.active]
        if not self.location_id or not selected_users:
            self.dlg = MDDialog(title='Team',
                                text='Bitte mindestens eine Person und eine Location auswählen!',
                                buttons=[MDFlatButton(text='Ok', on_release=lambda x: self.dlg.dismiss())])
            self.dlg.open()
            return
        try:
            response = values.session.post(f'{values.backend_url}actors/new-team',
                                           json={'location_id': self.location_id,
                                                 'actor_ids': selected_users}, timeout=10)
            if response.status_code == 200:
                self.get_departments_from_server(self.location_id)

                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'chat'
                print([a['artist_name'] for a in response.json()['actors']])
                values.set_team_of_actors(response.json())
                print([a['artist_name'] for a in values.team_of_actors['actors']])
                values.store.put('team_of_actors', id=values.team_of_actors['id'])
                print(f'....................................................... {values.store.get("team_of_actors")["id"]=}')
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


class CustomLabel(Label):
    text = StringProperty('')

    def on_texture_size(self, *args):
        self.width = min(self.texture_size[0], Window.width * 0.8)
        self.text_size = (self.width, None)


class MessageBubble(AnchorLayout):
    text = StringProperty('')  # Definieren Sie die text-Eigenschaft
    mode = StringProperty('incoming')  # Definieren Sie die Mode-Eigenschaft (incoming, outgoing, info

    def __init__(self, message, mode: Literal['incoming', 'outgoing', 'info'] = 'incoming', **kwargs):
        super(MessageBubble, self).__init__(**kwargs)
        self.mode = mode
        self.text = message

'#aaaaaa'
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

        self.dlg = None

    def on_enter(self, *args):
        if values.connect_to_past_ws:
            response = values.session.post(f'{values.backend_url}actors/set_all_messages_to_unsent',
                                           params={'team_of_actors_id': values.team_of_actors['id']})
            if response.status_code != 200:
                print(f'Fehler in set_all_messages_to_unsent: {response.status_code=}')
                print(f'.......................... {response.json()}')
            self.create_connection_service(False)
            values.connect_to_past_ws = False

    @mainthread
    def ws_opened(self, department_id):
        print(f'{department_id=}')
        if not self.chat_tabs.get('common_chat'):
            new_chat_tab = ChatTab(tab_label_text='Chat', osc_client=self.client,
                                   notification_client=self.notification_client, tab_pos=0)
            self.chat_tabs['common_chat'] = new_chat_tab
            self.ids.chat_tabs.add_widget(new_chat_tab)

    def on_tab_switch(self, *args):
        print(args)

    def create_connection_service(self, with_greeting=True):
        greeting = 'Hallo! Wir sind im Haus. 😊' if with_greeting else ''
        self.client.send_message(b'/connect',
                                 [greeting.encode('utf-8'), values.ws_url.encode('utf-8'),
                                        values.token.encode('utf-8'),
                                        values.team_of_actors['id'].encode('utf-8')])

    @mainthread
    def on_message(self, message):
        message_dict = json.loads(message.decode('utf-8'))
        print(f'on_message() >>>>>>>>>>>>>>>>>>>>>>>>>> {message_dict=}')
        timestamp = message_dict.get('timestamp', 'kein timestamp')
        send_confirmation = message_dict.get('send_confirmation')
        sender_id = message_dict.get('sender_id')
        receiver_id = message_dict.get('receiver_id')
        department_id = message_dict.get('department_id')
        message = message_dict.get('message')
        joined = message_dict.get('joined')
        left = message_dict.get('left')

        # Tabs müssen wiederhergestellt werden, wenn die App während einer Session neu gestartet wird:
        if department_id and not self.chat_tabs.get(department_id):
            joined_message = f"{values.departments_of_location[department_id]['name']} hat den Chat betreten."
            label = MessageBubble(message=joined_message, mode='info')
            self.chat_tabs['common_chat'].ids.output.add_widget(label)
            new_chat_tab = ChatTab(tab_label_text=f'{values.departments_of_location[department_id]["name"]}',
                                   department_id=department_id, osc_client=self.client,
                                   notification_client=self.notification_client, tab_pos=len(self.chat_tabs))

            self.chat_tabs[department_id] = new_chat_tab
            self.ids.chat_tabs.add_widget(new_chat_tab)

        if send_confirmation:
            if not receiver_id:
                if sender_id == values.team_of_actors['id']:
                    for department_id, chat_tab in self.chat_tabs.items():
                        label_timestamp = MessageBubble(message=timestamp, mode='info')
                        chat_tab.ids.output.add_widget(label_timestamp)
                        label = MessageBubble(message=send_confirmation, mode='outgoing')
                        chat_tab.ids.output.add_widget(label)
                else:
                    response = values.session.get(f'{values.backend_url}actors/team_of_actors',
                                                  params={'team_of_actors_id': sender_id}, timeout=10)
                    sender = response.json() if response.status_code == 200 else None
                    names = ', '.join([a['artist_name'] for a in sender['actors']]) if sender else ''
                    new_text = f"[{names}]\n{send_confirmation}"
                    for department_id, chat_tab in self.chat_tabs.items():
                        label_timestamp = MessageBubble(message=timestamp, mode='info')
                        chat_tab.ids.output.add_widget(label_timestamp)
                        label = MessageBubble(message=new_text, mode='outgoing')
                        chat_tab.ids.output.add_widget(label)
            else:
                label_timestamp_receiver_tab = MessageBubble(message=timestamp, mode='info')
                label_timestamp_common_tab = MessageBubble(message=timestamp, mode='info')
                if sender_id == values.team_of_actors['id']:
                    new_text_receiver_tab = f"{send_confirmation}"
                    new_text_common_tab = (f"{values.departments_of_location[receiver_id]['name']}: "
                                           f"{send_confirmation}")
                    label_receiver_tab = MessageBubble(message=new_text_receiver_tab, mode='outgoing')
                    label_common_tab = MessageBubble(message=new_text_common_tab, mode='outgoing')
                    self.chat_tabs[receiver_id].ids.output.add_widget(label_timestamp_receiver_tab)
                    self.chat_tabs[receiver_id].ids.output.add_widget(label_receiver_tab)
                    self.chat_tabs['common_chat'].ids.output.add_widget(label_timestamp_common_tab)
                    self.chat_tabs['common_chat'].ids.output.add_widget(label_common_tab)
                else:
                    response = values.session.get(f'{values.backend_url}actors/team_of_actors',
                                                  params={'team_of_actors_id': sender_id}, timeout=10)
                    sender = response.json() if response.status_code == 200 else None
                    names = ', '.join([a['artist_name'] for a in sender['actors']]) if sender else ''
                    new_text_receiver_tab = f"[{names}]\n{send_confirmation}"
                    new_text_common_tab = (f"[{names}]\n{values.departments_of_location[receiver_id]['name']}: "
                                           f"{send_confirmation}")
                    label_receiver_tab = MessageBubble(message=new_text_receiver_tab, mode='outgoing')
                    label_common_tab = MessageBubble(message=new_text_common_tab, mode='outgoing')
                    self.chat_tabs[receiver_id].ids.output.add_widget(label_timestamp_receiver_tab)
                    self.chat_tabs[receiver_id].ids.output.add_widget(label_receiver_tab)
                    self.chat_tabs['common_chat'].ids.output.add_widget(label_timestamp_common_tab)
                    self.chat_tabs['common_chat'].ids.output.add_widget(label_common_tab)
        elif message:
            if department_id:
                new_text_receiver_tab = f"{message}"
                new_text_common_tab = f"{values.departments_of_location[department_id]['name']}: {message}"
                label_receiver_tab = MessageBubble(message=new_text_receiver_tab, mode='incoming')
                label_common_tab = MessageBubble(message=new_text_common_tab, mode='incoming')
                self.chat_tabs['common_chat'].ids.output.add_widget(label_common_tab)
                self.chat_tabs[department_id].ids.output.add_widget(label_receiver_tab)
            else:
                ...
        elif joined:
            if department_id and not self.chat_tabs.get(department_id):
                joined_message = f"{values.departments_of_location[department_id]['name']} hat den Chat betreten."
                label_common_tab = MessageBubble(message=joined_message, mode='info')
                self.chat_tabs['common_chat'].ids.output.add_widget(label_common_tab)
                new_chat_tab = ChatTab(tab_label_text=f'{values.departments_of_location[department_id]["name"]}',
                                       department_id=department_id, osc_client=self.client,
                                       notification_client=self.notification_client, tab_pos=len(self.chat_tabs))

                self.chat_tabs[department_id] = new_chat_tab
                self.ids.chat_tabs.add_widget(new_chat_tab)
            else:
                ...
        elif left:
            if department_id:
                left_message = f"{values.departments_of_location[department_id]['name']} hat den Chat verlassen."
                label_common_tab = MessageBubble(message=left_message, mode='info')
                label_common_tab.text = left_message
                self.chat_tabs['common_chat'].ids.output.add_widget(label_common_tab)
                tab_position = self.chat_tabs[department_id].tab_pos
                for tab in self.chat_tabs.values():
                    if tab.tab_pos > tab_position:
                        tab.tab_pos -= 1
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

    def logout(self, *args):
        if self.dialog_exit:
            self.dialog_exit.dismiss(force=True)
            self.dialog_exit = None
        try:
            response = values.session.get(f'{values.backend_url}connection_test')
        except Exception as e:
            print(f'..................................... {e=}')
            self.dlg = MDDialog(title='Logout',
                                text='Der Server ist nicht erreichbar. Bitte stellen Sie sicher, '
                                     'dass eine Verbindung zum Netzwerk besteht.',
                                buttons=[MDFlatButton(text='Ok', on_release=lambda x: self.dlg.dismiss())])
            self.dlg.open()
            return

        response_all_messages = values.session.get(f'{values.backend_url}actors/session_messages',
                                                   params={'team_of_actors_id': values.team_of_actors['id']})
        print(f'................... {response_all_messages.json()=}')
        self.client.send_message(b'/close_connection',
                                 ['Wir verabschieden uns für heute. Danke für die Unterstützung! 👋'.encode('utf-8')])

        if platform == 'android' and values.service:
            values.service.stop(values.mActivity)

        for tab in self.ids.chat_tabs.get_tab_list():
            print(f'{tab=}')
            self.ids.chat_tabs.remove_widget(tab)

        self.chat_tabs = {}

        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        print(f'{threading.active_count()=}')

        values.store.put('team_of_actors', id=None)
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
