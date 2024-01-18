import requests
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
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


class CreateTeam(Screen):
    pass


class ClownControllApp(App):
    def build(self):
        Window.clearcolor = (0.2, 0.2, 0.2, 1)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CreateTeam(name='second'))
        return sm


if __name__ == '__main__':
    ClownControllApp().run()
