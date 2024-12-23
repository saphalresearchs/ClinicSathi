
from .models import Notification

from django.core.mail import send_mail
from .models import Notification

def send_email_and_notification(recipient, subject, message, event_type):
    """
    Send an email to the recipient and create an in-app notification.
    """
    # Send email
    if recipient.email:
        send_mail(
            subject=subject,
            message=message,
            from_email='programmersaphal@gmail.com',
            recipient_list=[recipient.email],
            fail_silently=False,
        )

    # Create an in-app notification
    notification = Notification.objects.create(
        recipient=recipient,
        event_type=event_type,
        subject=subject,
        message=message
    )

    return notification
