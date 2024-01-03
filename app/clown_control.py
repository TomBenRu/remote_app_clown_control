from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget


class RemoteLogin(BoxLayout):
    orientation = 'vertical'

    def connect_to_server(self):
        ...

    def send_message(self):
        ...


class RemoteApp(App):
    def build(self):
        return RemoteLogin()


if __name__ == '__main__':
    RemoteApp().run()
