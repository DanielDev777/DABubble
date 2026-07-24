import os

from django.core.exceptions import ImproperlyConfigured

_UNSET = object()


def get_env(name, default=_UNSET, required=False):
    """Read an environment variable. Fail loudly if a required one is missing."""
    value = os.environ.get(name, _UNSET)
    if value is _UNSET:
        if required:
            raise ImproperlyConfigured(f"Required environment variable {name!r} is not set.")
        if default is _UNSET:
            return None
        return default
    return value


def get_bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list_env(name, default=None):
    value = os.environ.get(name)
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]
