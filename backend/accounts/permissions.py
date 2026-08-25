from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    """Allow access only to authenticated Django superusers."""

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_superuser)
