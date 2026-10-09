from django.contrib import admin
from .models import Identity, DeviceBinding, LedgerAnchor, Policy, AccessGrant, Session

@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "did", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email", "did")

@admin.register(DeviceBinding)
class DeviceBindingAdmin(admin.ModelAdmin):
    list_display = ("device_id", "identity", "is_active", "bound_at")
    list_filter = ("is_active",)
    search_fields = ("device_id", "identity__username")

@admin.register(LedgerAnchor)
class LedgerAnchorAdmin(admin.ModelAdmin):
    list_display = ("block_index", "event_type", "identity", "anchored_at")
    list_filter = ("event_type",)
    search_fields = ("block_index", "identity__username", "block_hash")

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "resource", "action", "effect", "priority", "is_active")
    list_filter = ("action", "effect", "is_active", "resource")
    search_fields = ("name", "resource")

@admin.register(AccessGrant)
class AccessGrantAdmin(admin.ModelAdmin):
    list_display = ("identity", "policy", "is_active", "granted_at")
    list_filter = ("is_active",)
    search_fields = ("identity__username", "policy__name")

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_token", "identity", "ip_address", "is_active", "started_at")
    list_filter = ("is_active",)
    search_fields = ("session_token", "identity__username", "ip_address")
