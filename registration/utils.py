from django.core.mail import send_mail
from .models import Notification

def send_email_notification(recipient, subject, message, event_type):
    """
    Send an email to the recipient and log the notification.
    """
    if recipient.email:
        # Send the email
        send_mail(
            subject,
            message,
            'programmersaphal@gmail.com',  # Sender's email address
            [recipient.email]
        )

        # Log the notification
        Notification.objects.create(
            recipient=recipient,
            subject=subject,
            message=message,
            event_type=event_type
        )
