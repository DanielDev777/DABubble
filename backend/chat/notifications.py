from chat.models import Notification


def recipients(message, mentioned_users):
    """Map user id -> kind for everyone who should hear about `message`.

    Built in precedence order — dm, then reply, then mention — so the most
    specific label overwrites the less specific one. The actor is dropped last,
    however they got in.
    """
    by_user = {}
    channel = message.channel
    if channel.is_dm:
        for member in channel.members.all():
            by_user[member.id] = Notification.DM
    if message.parent_id:
        root = message.parent
        by_user[root.author_id] = Notification.REPLY
        earlier = (
            root.replies.exclude(pk=message.pk)
            .values_list("author_id", flat=True)
            .distinct()
        )
        for author_id in earlier:
            by_user[author_id] = Notification.REPLY
    for user in mentioned_users:
        by_user[user.id] = Notification.MENTION
    by_user.pop(message.author_id, None)
    return by_user


def sync_notifications(message, mentioned_users):
    """Reconcile `message`'s notifications with who should currently have one.

    Rows for people who are no longer recipients are deleted; rows whose reason
    changed are relabelled in place, keeping their pk and read state; missing
    ones are created unread.
    """
    wanted = recipients(message, mentioned_users)
    existing = {n.user_id: n for n in Notification.objects.filter(message=message)}

    gone = [note.id for user_id, note in existing.items() if user_id not in wanted]
    if gone:
        Notification.objects.filter(id__in=gone).delete()

    for user_id, kind in wanted.items():
        note = existing.get(user_id)
        if note is None:
            Notification.objects.create(
                message=message, user_id=user_id, kind=kind
            )
        elif note.kind != kind:
            note.kind = kind
            note.save(update_fields=["kind"])
