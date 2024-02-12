import time

from jnius import autoclass


Context = autoclass('android.content.Context')
print(f'{Context=}')
print('in notification_service.py')


class NotificationAndroid:
    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message

    def notify(self, *args):
        AndroidString = autoclass('java.lang.String')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        Drawable = autoclass('org.test.notify.R$drawable')  # jnius.autoclass("{}.R$drawable".format(service.getPackageName()))
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
    NotificationAndroid(title, message).notify()


if __name__ == '__main__':
    while True:
        print('notification service running...')
        time.sleep(1)
