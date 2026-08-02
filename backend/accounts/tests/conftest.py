import pytest


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    """Use the in-process channel layer for tests (no Redis needed)."""
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
    from channels.layers import channel_layers

    channel_layers.backends.clear()
    yield
    channel_layers.backends.clear()
