import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from chat.api.serializers import AttachmentSerializer, MessageSerializer
from chat.models import Attachment, Channel, Message

User = get_user_model()


@pytest.fixture
def message(db):
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    return Message.objects.create(channel=channel, author=owner, content="hi")


def _attach(message):
    return Attachment.objects.create(
        message=message,
        file=SimpleUploadedFile("a.png", b"data", content_type="image/png"),
        original_name="a.png",
        content_type="image/png",
        size=4,
    )


@pytest.mark.django_db
def test_attachment_serializer_shape(message, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    att = _attach(message)
    request = APIRequestFactory().get("/")
    data = AttachmentSerializer(att, context={"request": request}).data
    assert data["original_name"] == "a.png"
    assert data["content_type"] == "image/png"
    assert data["size"] == 4
    assert data["file"].startswith("http")


@pytest.mark.django_db
def test_message_serializer_includes_attachments(message, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    _attach(message)
    request = APIRequestFactory().get("/")
    data = MessageSerializer(message, context={"request": request}).data
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["original_name"] == "a.png"


@pytest.mark.django_db
def test_deleted_message_serializes_without_attachments(message, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    _attach(message)
    message.is_deleted = True
    message.save(update_fields=["is_deleted"])
    request = APIRequestFactory().get("/")
    data = MessageSerializer(message, context={"request": request}).data
    assert data["content"] == ""
    assert data["attachments"] == []
