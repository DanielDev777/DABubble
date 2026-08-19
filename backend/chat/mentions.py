import re

# An "@" only opens a mention at a word boundary: at the start of the text, or
# after whitespace/punctuation. This is what stops "noah@braun.com" from
# resolving. The character before the "@" is consumed by the match, so use
# match.end() to get the first character of the candidate name.
_MENTION_AT = re.compile(r"(?:^|[^\w@])@")


def _ends_cleanly(content, end):
    """True if the character after a matched name is not part of a longer word."""
    if end >= len(content):
        return True
    nxt = content[end]
    return not (nxt.isalnum() or nxt == "_")


def resolve_mentions(content, candidates):
    """Return the users from `candidates` named by "@Name" in `content`.

    Matching is case-insensitive and longest-name-first, so with candidates
    "Noah" and "Noah Braun" the text "@Noah Braun" resolves to "Noah Braun".
    Names may contain spaces, which is why this matches against a known list of
    candidates rather than guessing where a name ends. The result is
    de-duplicated, in order of first appearance.

    Pure: it performs no database access. Callers supply the candidates.
    """
    if not content:
        return []
    by_length = sorted(
        candidates, key=lambda user: len(user.full_name or ""), reverse=True
    )
    lowered = content.lower()
    found = []
    seen = set()
    for match in _MENTION_AT.finditer(content):
        start = match.end()
        for user in by_length:
            name = (user.full_name or "").lower()
            if not name or not lowered.startswith(name, start):
                continue
            if not _ends_cleanly(content, start + len(name)):
                continue
            if user.id not in seen:
                seen.add(user.id)
                found.append(user)
            break
    return found


def sync_mentions(message):
    """Make `message`'s Mention rows match its current content.

    Resolves against the members of the message's channel (for a DM, its two
    participants) and returns the resolved users. Diff-based on purpose: rows
    that survive an edit keep their primary keys, which Part 8b's notifications
    will depend on.
    """
    from chat.models import Mention

    users = resolve_mentions(message.content, message.channel.members.all())
    wanted = {user.id for user in users}
    existing = set(
        Mention.objects.filter(message=message).values_list("user_id", flat=True)
    )
    stale = existing - wanted
    if stale:
        Mention.objects.filter(message=message, user_id__in=stale).delete()
    Mention.objects.bulk_create(
        [Mention(message=message, user_id=uid) for uid in wanted - existing]
    )
    return users
