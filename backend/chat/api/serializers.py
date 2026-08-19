from rest_framework import serializers

from accounts.api.serializers import UserSerializer
from chat.models import Attachment, Channel, Message
from chat.reactions import ALLOWED_REACTIONS


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = (
            "id", "name", "description", "owner",
            "member_count", "is_member", "created_at",
        )
        read_only_fields = (
            "id", "owner", "member_count", "is_member", "created_at",
        )

    def get_member_count(self, obj):
        return obj.members.count()

    def get_is_member(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(id=request.user.id).exists()

    def validate_name(self, value):
        if value.lower().startswith("dm:"):
            raise serializers.ValidationError("This channel name is reserved.")
        qs = Channel.objects.filter(name__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A channel with this name already exists.")
        return value


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("id", "file", "original_name", "content_type", "size")
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_count = serializers.SerializerMethodField()
    last_reply_at = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()
    content = serializers.CharField(
        required=False, allow_blank=True, max_length=4000, default=""
    )

    class Meta:
        model = Message
        fields = (
            "id", "channel", "parent", "author", "content",
            "created_at", "edited_at", "is_deleted", "attachments",
            "reply_count", "last_reply_at", "reactions", "mentions",
        )
        read_only_fields = (
            "id", "channel", "parent", "author", "created_at", "edited_at",
            "is_deleted", "attachments", "reply_count", "last_reply_at", "reactions",
            "mentions",
        )

    def get_mentions(self, obj):
        return [
            {"id": m.user_id, "full_name": m.user.full_name}
            for m in obj.mentions.all()
        ]

    def get_reactions(self, obj):
        user = getattr(self.context.get("request"), "user", None)
        me = user.id if user is not None and user.is_authenticated else None
        buckets = {}
        for r in obj.reactions.all():
            bucket = buckets.get(r.emoji)
            if bucket is None:
                bucket = {"emoji": r.emoji, "count": 0, "reacted": False, "users": []}
                buckets[r.emoji] = bucket
            bucket["count"] += 1
            bucket["users"].append({"id": r.user_id, "full_name": r.user.full_name})
            if r.user_id == me:
                bucket["reacted"] = True
        order = {emoji: i for i, emoji in enumerate(ALLOWED_REACTIONS)}
        return sorted(buckets.values(), key=lambda b: order.get(b["emoji"], 999))

    def get_reply_count(self, obj):
        val = getattr(obj, "_reply_count", None)
        return val if val is not None else obj.replies.count()

    def get_last_reply_at(self, obj):
        if hasattr(obj, "_last_reply_at"):
            return obj._last_reply_at
        last = obj.replies.order_by("-created_at").first()
        return last.created_at if last else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["content"] = ""
            data["attachments"] = []
            data["mentions"] = []
        return data


class DmSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    def get_other_user(self, channel):
        request = self.context.get("request")
        me = request.user if request else None
        other = None
        for member in channel.members.all():
            if me is None or member.id != me.id:
                other = member
                break
        if other is None:
            other = me  # self-DM
        return UserSerializer(other, context=self.context).data

    def get_last_message(self, channel):
        msg = (
            channel.messages.filter(is_deleted=False)
            .order_by("-created_at")
            .first()
        )
        if msg is None:
            return None
        return {"content": msg.content, "created_at": msg.created_at}
