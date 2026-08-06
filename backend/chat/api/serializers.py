from rest_framework import serializers

from accounts.api.serializers import UserSerializer
from chat.models import Attachment, Channel, Message


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
    content = serializers.CharField(
        required=False, allow_blank=True, max_length=4000, default=""
    )

    class Meta:
        model = Message
        fields = (
            "id", "channel", "author", "content",
            "created_at", "edited_at", "is_deleted", "attachments",
        )
        read_only_fields = (
            "id", "author", "created_at", "edited_at", "is_deleted", "attachments",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["content"] = ""
            data["attachments"] = []
        return data
