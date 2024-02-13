import time

from jnius import autoclass
from oscpy.server import OSCThreadServer

SERVER = OSCThreadServer()


class NotificationService:
    def __init__(self):
        print('................... in notification_service.py')

        self.server = SERVER
        self.server.listen(address=b'localhost', port=3004, default=True)

        self.server.bind(b'/notify', self.notify_to_bar)

        self.Context = autoclass('android.content.Context')
        self.Intent = autoclass('android.content.Intent')
        self.PendingIntent = autoclass('android.app.PendingIntent')
        self.AndroidString = autoclass('java.lang.String')
        self.NotificationBuilder = autoclass('android.app.Notification$Builder')
        self.Notification = autoclass('android.app.Notification')
        self.service_name = 'S1'
        self.package_name = 'com.something'
        self.service = autoclass('org.kivy.android.PythonService').mService
        # Previous version of Kivy had a reference to the service like below.
        # self.service = jnius.autoclass('{}.Service{}'.format(package_name, service_name)).mService
        self.PythonActivity = autoclass('org.kivy.android' + '.PythonActivity')
        self.notification_service = self.service.getSystemService(
            self.Context.NOTIFICATION_SERVICE)
        self.app_context = self.service.getApplication().getApplicationContext()
        self.notification_builder = self.NotificationBuilder(self.app_context)
        self.title = self.AndroidString("EzTunes".encode('utf-8'))
        self.message = self.AndroidString("Ready to play music.".encode('utf-8'))
        self.app_class = self.service.getApplication().getClass()
        self.notification_intent = self.Intent(self.app_context, self.PythonActivity)
        self.notification_intent.setFlags(self.Intent.FLAG_ACTIVITY_CLEAR_TOP |
                                     self.Intent.FLAG_ACTIVITY_SINGLE_TOP | self.Intent.FLAG_ACTIVITY_NEW_TASK)
        self.notification_intent.setAction(self.Intent.ACTION_MAIN)
        self.notification_intent.addCategory(self.Intent.CATEGORY_LAUNCHER)
        self.intent = self.PendingIntent.getActivity(self.service, 0, self.notification_intent, 0)
        self.notification_builder.setContentTitle(self.title)
        self.notification_builder.setContentText(self.message)
        self.notification_builder.setContentIntent(self.intent)
        self.Drawable = autoclass(f"{self.service.getPackageName()}.R$drawable")
        self.icon = self.Drawable.icon  # getattr(self.Drawable, 'icon')  # Drawable.icon
        self.notification_builder.setSmallIcon(self.icon)
        self.notification_builder.setAutoCancel(True)
        self.new_notification = self.notification_builder.getNotification()

    def notify_to_bar(self):
        print('................... in notify_to_bar()')
        # Below sends the notification to the notification bar; nice but not a foreground service.
        self.notification_service.notify(0, self.new_notification)
        # self.service.startForeground(1, self.new_notification)
        print('................... finished notify_to_bar()')


class NotificationAndroid:
    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message

    def notify(self, *args):
        AndroidString = autoclass('java.lang.String')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        service = autoclass('org.kivy.android.PythonService').mService
        Drawable = autoclass(f"{service.getPackageName()}.R$drawable")  # jnius.autoclass("{}.R$drawable".format(service.getPackageName()))
        icon = Drawable.icon
        notification_builder = NotificationBuilder(PythonActivity.mActivity)
        notification_builder.setContentTitle(AndroidString(self.title.encode('utf-8')))
        notification_builder.setContentText(AndroidString(self.message.encode('utf-8')))
        notification_builder.setSmallIcon(icon)
        notification_builder.setAutoCancel(True)
        Context = autoclass('android.content.Context')
        notification_service = PythonActivity.mActivity.getSystemService(Context.NOTIFICATION_SERVICE)
        notification_service.notify(0, notification_builder.build())


def notify_android(title: str, message: str):
    try:
        NotificationAndroid(title, message).notify()
    except Exception as e:
        print(f'Exception in notify_android(): {e}')


SERVER.listen(address=b'localhost', port=3004, default=True)

SERVER.bind(b'/notify', lambda: notify_android('ClownCall', 'New message'))


if __name__ == '__main__':
    print('notification service starting...')
    # notification_service = NotificationService()
    while True:
        print('notification service running...')
        time.sleep(1)
