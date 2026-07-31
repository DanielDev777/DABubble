from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Reset all users' presence connection counts to 0 (run at startup)."

    def handle(self, *args, **options):
        updated = User.objects.filter(presence_connections__gt=0).update(
            presence_connections=0
        )
        self.stdout.write(f"Reset presence for {updated} user(s).")
