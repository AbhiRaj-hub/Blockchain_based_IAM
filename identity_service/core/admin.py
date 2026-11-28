from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import AccessGrant, DeviceBinding, Identity, LedgerAnchor, PendingAnchor, Policy, Session


@admin.register(Identity)
class IdentityAdmin(UserAdmin):
    model = Identity
    list_display = ["username", "did", "role", "clearance_level", "status", "department"]
    list_filter = ["role", "status", "department"]
    search_fields = ["username", "did", "email"]
    readonly_fields = ["id", "did", "created_at", "updated_at"]
    fieldsets = UserAdmin.fieldsets + (
        (
            "IAM attributes",
            {
                "fields": (
                    "did", "public_key", "role", "clearance_level",
                    "department", "status",
                )
            },
        ),
    )


@admin.register(DeviceBinding)
class DeviceBindingAdmin(admin.ModelAdmin):
    list_display = ["identity", "device_fingerprint", "trust_level", "last_seen"]
    list_filter = ["trust_level"]


@admin.register(LedgerAnchor)
class LedgerAnchorAdmin(admin.ModelAdmin):
    list_display = ["identity", "event_type", "block_hash", "anchored_at"]
    list_filter = ["event_type"]
    readonly_fields = [f.name for f in LedgerAnchor._meta.fields]  # audit trail: view only

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "resource", "action", "effect", "min_clearance", "priority", "is_active"]
    list_filter = ["effect", "is_active"]
    search_fields = ["name", "resource"]


@admin.register(AccessGrant)
class AccessGrantAdmin(admin.ModelAdmin):
    list_display = ["identity", "resource", "action", "status", "issued_at", "expires_at"]
    list_filter = ["status"]
    readonly_fields = ["token", "issued_at"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["identity", "is_active", "created_at", "expires_at", "ip_address"]
    list_filter = ["is_active"]


@admin.register(PendingAnchor)
class PendingAnchorAdmin(admin.ModelAdmin):
    list_display = ["identity", "event_type", "attempts", "created_at"]
    readonly_fields = [f.name for f in PendingAnchor._meta.fields]

    def has_add_permission(self, request):
        return False
