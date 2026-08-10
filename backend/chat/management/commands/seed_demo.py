from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chat.models import Channel, ChannelMembership, Message, Reaction

User = get_user_model()

DEMO_USERS = [
    ("demo-alice@demo.local", "Alice Demo", "bob"),
    ("demo-bob@demo.local", "Bob Demo", "quiff"),
    ("demo-carol@demo.local", "Carol Demo", "long-hair"),
    ("demo-dan@demo.local", "Dan Demo", "dark-hair"),
    ("demo-eve@demo.local", "Eve Demo", "wavy-hair"),
]

DEMO_CHANNELS = [
    ("General", "Company-wide chatter"),
    ("Dev", "Engineering discussion"),
    ("Random", "Off-topic and fun"),
]

SCRIPTS = {
    "General": [
        (0, "Morning everyone! 👋"),
        (1, "Morning! Coffee first, then standup."),
        (2, "Welcome to DABubble — this is the General channel."),
        (3, "Messages, threads, and reactions all work here."),
        (0, "Try reacting to a message or opening a thread!"),
    ],
    "Dev": [
        (1, "Pushed the auth refactor, please review."),
        (3, "Nice — the cookie-JWT flow looks clean."),
        (1, "Thanks! The whole backend suite is green."),
        (4, "Deploying to staging this afternoon."),
    ],
    "Random": [
        (2, "Anyone up for lunch?"),
        (4, "Always. Tacos?"),
        (2, "🌮 say no more"),
    ],
}


class Command(BaseCommand):
    help = "Seed a demo workspace (idempotent)."

    def handle(self, *args, **options):
        users = self._users()
        channels = self._channels(users)
        for channel in channels:
            self._conversation(channel, users)
        self.stdout.write("Demo workspace ready.")

    def _users(self):
        users = []
        for email, name, avatar in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"full_name": name, "default_avatar": avatar},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            users.append(user)
        return users

    def _channels(self, users):
        owner = users[0]
        channels = []
        for name, description in DEMO_CHANNELS:
            channel, _ = Channel.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "owner": owner,
                    "is_demo": True,
                },
            )
            if not channel.is_demo:
                channel.is_demo = True
                channel.save(update_fields=["is_demo"])
            for user in users:
                ChannelMembership.objects.get_or_create(channel=channel, user=user)
            channels.append(channel)
        return channels

    def _conversation(self, channel, users):
        if channel.messages.exists():
            return
        msgs = [
            Message.objects.create(channel=channel, author=users[i], content=text)
            for i, text in SCRIPTS.get(channel.name, [])
        ]
        if channel.name == "General" and len(msgs) >= 3:
            root = msgs[2]
            for i, text in [(3, "Great to have you here!"), (0, "Ask us anything.")]:
                Message.objects.create(
                    channel=channel, author=users[i], content=text, parent=root
                )
        if msgs:
            Reaction.objects.get_or_create(message=msgs[0], user=users[1], emoji="👍")
            Reaction.objects.get_or_create(message=msgs[0], user=users[2], emoji="👍")
            if len(msgs) >= 2:
                Reaction.objects.get_or_create(
                    message=msgs[1], user=users[3], emoji="🎉"
                )
