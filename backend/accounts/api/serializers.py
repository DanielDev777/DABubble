import random

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from accounts.models import DEFAULT_AVATAR_SLUGS, User


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "avatar", "avatar_url",
            "default_avatar", "is_guest", "is_online",
        )
        read_only_fields = (
            "id", "email", "full_name", "avatar", "avatar_url",
            "default_avatar", "is_guest",
        )


class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=75)
    last_name = serializers.CharField(max_length=75)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    consent = serializers.BooleanField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_consent(self, value):
        if value is not True:
            raise serializers.ValidationError("You must accept the privacy policy.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        full_name = (
            f"{validated_data['first_name'].strip()} "
            f"{validated_data['last_name'].strip()}"
        ).strip()
        return User.objects.create_user(
            email=validated_data["email"],
            full_name=full_name,
            password=validated_data["password"],
            privacy_accepted_at=timezone.now(),
            default_avatar=random.choice(DEFAULT_AVATAR_SLUGS),
        )


MAX_AVATAR_BYTES = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "avatar", "default_avatar")

    def validate_avatar(self, image):
        if image.size > MAX_AVATAR_BYTES:
            raise serializers.ValidationError("Image must be 2 MB or smaller.")
        content_type = getattr(image, "content_type", None)
        if content_type not in ALLOWED_AVATAR_TYPES:
            raise serializers.ValidationError(
                "Only JPEG, PNG, or WEBP images are allowed."
            )
        return image

    def update(self, instance, validated_data):
        if "full_name" in validated_data:
            instance.full_name = validated_data["full_name"]
        if validated_data.get("avatar"):
            instance.avatar = validated_data["avatar"]
            instance.default_avatar = None
            instance.avatar_url = None
        elif validated_data.get("default_avatar"):
            instance.default_avatar = validated_data["default_avatar"]
            instance.avatar = None
            instance.avatar_url = None
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs
