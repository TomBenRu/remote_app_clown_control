from uuid import UUID

import requests
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from pydantic import BaseModel


class Values:
    def __init__(self):
        self.session = requests.Session()
        self.backend_url = "http://localhost:8000/"

    def set_session_token(self, token: str):
        self.session.headers.update({'Authorization': f'Bearer {token}'})


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
                self.manager.current = 'second'
            else:
                self.login_error.text = 'Username oder Passwort ungültig!'
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class CreateTeamScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = GridLayout(cols=2, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.users = []
        self.checkboxes = []
        self.confirm_button = Button(text='Confirm Selection')
        self.confirm_button.bind(on_release=self.confirm_selection)
        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        scrollview.add_widget(self.layout)
        self.add_widget(scrollview)

    def on_enter(self, *args):
        self.users = self.get_users()
        for user in self.users:
            checkbox = CheckBox()
            self.checkboxes.append(checkbox)
            self.layout.add_widget(Label(text=f'{user["f_name"]} {user["l_name"]}'))
            self.layout.add_widget(checkbox)
        self.locations = self.get_locations()
        self.location_spinner = Spinner(
            text='Select a Location',
            values=[f"{i+1}.: {l['name']}" for i, l in enumerate(self.locations)])
        self.layout.add_widget(self.location_spinner)
        self.layout.add_widget(self.confirm_button)
        print(self.users)
        print(self.locations)

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
        try:
            location_id = self.locations[int(self.location_spinner.text.split('.:')[0]) - 1]['id']
            response = values.session.post(f'{values.backend_url}actors/new-team',
                                           json={'location_id': location_id, 'user_ids': selected_users}, timeout=10)
            if response.status_code == 200:
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'third'
            else:
                self.layout.add_widget(Label(text='Fehler bei der Teamerstellung!'))
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class ChatScreen(Screen):
    ...


class ClownControllApp(App):
    def build(self):
        Window.clearcolor = (0.2, 0.2, 0.2, 1)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeamScreen(name='second'))
        sm.add_widget(ChatScreen(name='third'))
        return sm


if __name__ == '__main__':
    ClownControllApp().run()
