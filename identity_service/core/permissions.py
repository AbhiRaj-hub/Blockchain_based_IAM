from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view)->bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")

class IsAdminOrAuditor(permissions.BasePermission):
    def has_permission(self, request, view)->bool:
        return bool(request.user and request.user.is_authenticated and request.user.role in ["admin", "auditor"])

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj)->bool:
        if request.user.role == "admin":
            return True
        if hasattr(obj, "identity"):
            return obj.identity == request.user
        return obj == request.user
