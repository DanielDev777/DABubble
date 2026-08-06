from rest_framework import serializers

ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 10


def validate_attachment(uploaded_file):
    """Validate a single uploaded attachment; raise ValidationError if invalid."""
    if uploaded_file.size > MAX_ATTACHMENT_BYTES:
        raise serializers.ValidationError(
            f"'{uploaded_file.name}' exceeds the 10 MB limit."
        )
    content_type = getattr(uploaded_file, "content_type", None)
    if content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise serializers.ValidationError(
            f"'{uploaded_file.name}' has an unsupported type ({content_type})."
        )
    return uploaded_file
