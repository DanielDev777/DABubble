from rest_framework import permissions


class IsChannelOwner(permissions.BasePermission):
    message = "Only the channel owner may perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id
