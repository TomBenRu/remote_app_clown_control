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
title = AndroidString("EzTunes".encode('utf-8'))
print(f'................ {title=}')
message = AndroidString("Ready to play music.".encode('utf-8'))
print(f'................ {message=}')
app_class = service.getApplication().getClass()
print(f'................ {app_class=}')
notification_intent = Intent(app_context, PythonActivity)
notification_intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP |
                             Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
notification_intent.setAction(Intent.ACTION_MAIN)
notification_intent.addCategory(Intent.CATEGORY_LAUNCHER)
print(f'................ {notification_intent=}')
intent = PendingIntent.getActivity(service, 0, notification_intent, 0)
print(f'................ {intent=}')
notification_builder.setContentTitle(title)
notification_builder.setContentText(message)
notification_builder.setContentIntent(intent)
print(f'................ {notification_builder=}')
Drawable = autoclass("{}.R$drawable".format(service.getPackageName()))
print(f'................ {Drawable=}')
icon = getattr(Drawable, 'icon')
print(f'................ {icon=}')
notification_builder.setSmallIcon(icon)
notification_builder.setAutoCancel(True)
new_notification = notification_builder.getNotification()
#Below sends the notification to the notification bar; nice but not a foreground service.
#notification_service.notify(0, new_noti)
service.startForeground(1, new_notification)


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
