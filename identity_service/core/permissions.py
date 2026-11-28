from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsAdminOrAuditorReadOnly(BasePermission):
    """
    Admins: full access. Auditors: read-only (they must see everything
    but never be able to change it). Everyone else: denied.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin":
            return True
        return request.user.role == "auditor" and request.method in SAFE_METHODS


class IsSelfOrAdmin(BasePermission):
    """Identities may read their own record; admins may touch any."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        owner = getattr(obj, "identity", obj)
        return owner.id == request.user.id and request.method in SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """Owner (or admin) may read and act on their own sessions."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj.identity_id == request.user.id
