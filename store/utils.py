# store/utils.py

from django.core.mail import send_mail

# Send email notifications to all users when a notification is for all users
def send_notification_email(notification):
    if notification.for_all:
        for user in notification.user.all():
            send_mail(
                'New Notification from Elie Tech',
                notification.message,
                'no-reply@elietech.com',
                [user.email],
                fail_silently=False,
            )
