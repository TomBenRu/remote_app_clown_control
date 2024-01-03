from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout


Window.softinput_mode = 'below_target'


class RemoteLogin(BoxLayout):

    def connect_to_server(self):
        ...

    def send_message(self):
        ...


class RemoteApp(App):
    def build(self):
        return RemoteLogin()


if __name__ == '__main__':
    RemoteApp().run()
