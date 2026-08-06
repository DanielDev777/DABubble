import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from chat.models import Attachment, Channel, Message

User = get_user_model()


@pytest.fixture
def message(db):
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    return Message.objects.create(channel=channel, author=owner, content="hi")


@pytest.mark.django_db
def test_attachment_links_to_message(message, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    att = Attachment.objects.create(
        message=message,
        file=SimpleUploadedFile("a.png", b"data", content_type="image/png"),
        original_name="a.png",
        content_type="image/png",
        size=4,
    )
    assert message.attachments.filter(id=att.id).exists()
    assert att.original_name == "a.png"
    assert att.size == 4
    assert att.file.name.startswith("attachments/")
