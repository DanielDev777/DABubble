from rest_framework import serializers

from accounts.api.serializers import UserSerializer
from chat.models import Channel, Message


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


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id", "channel", "author", "content",
            "created_at", "edited_at", "is_deleted",
        )
        read_only_fields = ("id", "author", "created_at", "edited_at", "is_deleted")

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        if len(value) > 4000:
            raise serializers.ValidationError("Message too long (max 4000 characters).")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["content"] = ""
        return data
