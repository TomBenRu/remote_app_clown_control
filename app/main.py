from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


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
