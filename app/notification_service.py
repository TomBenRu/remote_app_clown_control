import time

from jnius import autoclass


print('................... in notification_service.py')
Context = autoclass('android.content.Context')
print(f'................ {Context=}')
Intent = autoclass('android.content.Intent')
print(f'................ {Intent=}')
PendingIntent = autoclass('android.app.PendingIntent')
print(f'................ {PendingIntent=}')
AndroidString = autoclass('java.lang.String')
print(f'................ {AndroidString=}')
NotificationBuilder = autoclass('android.app.Notification$Builder')
print(f'................ {NotificationBuilder=}')
Notification = autoclass('android.app.Notification')
print(f'................ {Notification=}')
service_name = 'S1'
package_name = 'com.something'
service = autoclass('org.kivy.android.PythonService').mService
print(f'................ {service=}')
PythonActivity = autoclass('org.kivy.android' + '.PythonActivity')
print(f'................ {PythonActivity=}')
notification_service = service.getSystemService(Context.NOTIFICATION_SERVICE)
print(f'................ {notification_service=}')
app_context = service.getApplication().getApplicationContext()
notification_builder = NotificationBuilder(app_context)
print(f'................ {notification_builder=}')
title = AndroidString("EzTunes".encode('utf-8'))
print(f'................ {title=}')
message = AndroidString("Ready to play music.".encode('utf-8'))
print(f'................ {message=}')


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
