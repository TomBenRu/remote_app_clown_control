import requests
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label


class Values:
    def __init__(self):
        self.token: str | None = None

    def set_token(self, token: str):
        self.token = token


values = Values()


class LoginScreen(Screen):

    def validate_user(self):
        backend_url = "http://localhost:8000/"
        data = {'username': self.username.text, 'password': self.password.text}
        try:
            response = requests.post(f'{backend_url}token/', data, timeout=10)
            if response.status_code == 200 and response.json().get('status_code', 200) == 200:
                print(response.json())
                values.set_token(response.json().get('access_token'))
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

        self.session = requests.Session()

        self.layout = GridLayout(cols=2, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.users = []
        self.checkboxes = []
        self.confirm_button = Button(text='Confirm Selection')
        self.confirm_button.bind(on_release=self.confirm_selection)
        self.layout.add_widget(self.confirm_button)
        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        scrollview.add_widget(self.layout)
        self.add_widget(scrollview)

    def on_enter(self, *args):
        self.session.headers.update({'Authorization': f'Bearer {values.token}'})
        self.users = self.get_users()
        for user in self.users:
            checkbox = CheckBox()
            self.checkboxes.append(checkbox)
            self.layout.add_widget(Label(text=f'{user["f_name"]} {user["l_name"]}'))
            self.layout.add_widget(checkbox)
        self.layout.add_widget(self.confirm_button)

    def get_users(self):
        backend_url = "http://localhost:8000/"
        try:
            response = self.session.get(f'{backend_url}actors/all_actors', timeout=10)
            print(response.json())
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except requests.exceptions.RequestException as e:
            return []

    def confirm_selection(self, instance):
        selected_users = [user for checkbox, user in zip(self.checkboxes, self.users) if checkbox.active]
        backend_url = "http://localhost:8000/"
        data = {'users': selected_users}
        try:
            response = requests.post(f'{backend_url}new-team/', data, timeout=10)
            if response.status_code == 200:
                self.manager.transition = SlideTransition(direction="left")
                self.manager.current = 'third'
            else:
                self.layout.add_widget(Label(text='Fehler bei der Teamerstellung!'))
        except requests.exceptions.RequestException as e:
            self.layout.add_widget(Label(text=str(e)))


class ClownControllApp(App):
    def build(self):
        Window.clearcolor = (0.2, 0.2, 0.2, 1)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeamScreen(name='second'))
        return sm


if __name__ == '__main__':
    ClownControllApp().run()
