from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User


class Command(BaseCommand):
    help = "Delete guest accounts older than N days."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        stale = User.objects.filter(is_guest=True, date_joined__lt=cutoff)
        count = stale.count()
        stale.delete()
        self.stdout.write(
            f"Deleted {count} guest account(s) older than {days} day(s)."
        )
