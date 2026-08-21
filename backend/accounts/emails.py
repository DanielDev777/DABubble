from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from accounts.tokens import make_reset_link

SUBJECT = "DABubble – Passwort zurücksetzen"


def send_password_reset_email(user):
    """Mail the user a link to the frontend's reset-password screen."""
    body = render_to_string(
        "accounts/password_reset_email.txt",
        {"user": user, "reset_url": make_reset_link(user)},
    )
    send_mail(
        subject=SUBJECT,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
