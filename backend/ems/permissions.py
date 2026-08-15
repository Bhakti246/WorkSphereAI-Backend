from rest_framework.permissions import BasePermission


def user_roles(user):
    if not user or not user.is_authenticated:
        return set()
    return set(g.name for g in user.groups.all())


class RolePermission(BasePermission):
    """Allow access only to users in one of the allowed roles.

    Views may define `allowed_roles = ['HR', 'Manager']` attribute.
    If `allowed_roles` is not present, access is allowed (fallback to other checks).
    Superusers bypass checks.
    """

    def has_permission(self, request, view):
        allowed = getattr(view, 'allowed_roles', None)
        # If view does not set allowed_roles, don't block here
        if not allowed:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, 'is_superuser', False):
            return True

        roles = user_roles(user)
        return bool(roles.intersection(set(allowed)))
from rest_framework import permissions


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
