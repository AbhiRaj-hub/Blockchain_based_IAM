import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = [
    ("admin", "Admin"),
    ("auditor", "Auditor"),
    ("user", "User"),
]

ACTION_CHOICES = [
    ("read", "Read"),
    ("write", "Write"),
    ("delete", "Delete"),
    ("admin", "Admin"),
]

EFFECT_CHOICES = [
    ("allow", "Allow"),
    ("deny", "Deny"),
]

class Identity(AbstractUser):
    did = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    public_key = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "identity"
        verbose_name_plural = "identities"

    def __str__()->str:
        return f"{self.username} ({self.did})"

class DeviceBinding(models.Model):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255, blank=True, default="")
    device_fingerprint = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)
    bound_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-bound_at"]

    def __str__()->str:
        return f"Device {self.device_id} for {self.identity}"

class LedgerAnchor(models.Model):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="anchors")
    block_index = models.PositiveIntegerField()
    block_hash = models.CharField(max_length=64)
    event_type = models.CharField(max_length=50)
    anchored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-block_index"]

    def __str__()->str:
        return f"Anchor {self.block_index} ({self.event_type})"

class Policy(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")
    resource = models.CharField(max_length=120)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    effect = models.CharField(max_length=10, choices=EFFECT_CHOICES, default="allow")
    conditions = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Identity, on_delete=models.SET_NULL, null=True, related_name="created_policies")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "name"]
        verbose_name_plural = "policies"

    def __str__()->str:
        return self.name

class AccessGrant(models.Model):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="grants")
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="grants")
    granted_by = models.ForeignKey(Identity, on_delete=models.SET_NULL, null=True, related_name="issued_grants")
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-granted_at"]

    def __str__()->str:
        return f"Grant {self.policy.name} -> {self.identity}"

class Session(models.Model):
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="sessions")
    device = models.ForeignKey(DeviceBinding, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__()->str:
        return f"Session {self.session_token} ({self.identity})"
