import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Identity(AbstractUser):
    """
    The IAM subject record. Extends Django's AbstractUser so
    djangorestframework-simplejwt works out of the box, plus the
    fields the Policy engine and Access broker actually read.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"
        AUDITOR = "auditor", "Auditor"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    did = models.CharField(max_length=128, unique=True, editable=False)
    public_key = models.TextField(blank=True, help_text="PEM-encoded public key")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.EMPLOYEE)
    clearance_level = models.PositiveSmallIntegerField(default=1)  # 1 (lowest) - 5 (highest)
    department = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.did:
            import hashlib

            # DID derives from the public key; fall back to the record id
            # for accounts created without one (e.g. createsuperuser).
            seed = self.public_key or str(self.id)
            self.did = "did:secureaccess:" + hashlib.sha256(seed.encode()).hexdigest()[:16]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.did})"


class DeviceBinding(models.Model):
    class TrustLevel(models.TextChoices):
        TRUSTED = "trusted", "Trusted"
        UNRECOGNIZED = "unrecognized", "Unrecognized"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="devices")
    device_fingerprint = models.CharField(max_length=128)
    trust_level = models.CharField(
        max_length=16, choices=TrustLevel.choices, default=TrustLevel.UNRECOGNIZED
    )
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("identity", "device_fingerprint")

    def __str__(self):
        return f"{self.device_fingerprint} ({self.trust_level})"


class LedgerAnchor(models.Model):
    """
    Local pointer to a block on the Flask/MongoDB ledger service.
    Written only after the ledger confirms the block was appended.
    """

    class EventType(models.TextChoices):
        IDENTITY_CREATED = "identity_created"
        IDENTITY_UPDATED = "identity_updated"
        IDENTITY_SUSPENDED = "identity_suspended"
        IDENTITY_REVOKED = "identity_revoked"
        ACCESS_GRANTED = "access_granted"
        ACCESS_REVOKED = "access_revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="ledger_anchors")
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    block_hash = models.CharField(max_length=64)
    anchored_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} -> {self.block_hash[:10]}..."


class Policy(models.Model):
    """
    RBAC baseline (role + min_clearance) plus an ABAC overlay
    (conditions) evaluated at request time. See services/policy_engine.py.
    """

    class Effect(models.TextChoices):
        ALLOW = "allow", "Allow"
        DENY = "deny", "Deny"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    resource = models.CharField(max_length=128, help_text="e.g. 'finance.reports'")
    action = models.CharField(max_length=32, help_text="e.g. 'read', 'write', 'approve'")
    effect = models.CharField(max_length=8, choices=Effect.choices, default=Effect.ALLOW)
    allowed_roles = models.JSONField(default=list, help_text="List of Identity.Role values")
    min_clearance = models.PositiveSmallIntegerField(default=1)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "ABAC conditions, e.g. "
            '{"device_trust": ["trusted"], "hours": [8, 20]}'
        ),
    )
    priority = models.IntegerField(default=0, help_text="Higher priority evaluated first")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority"]

    def __str__(self):
        return f"{self.name} [{self.effect}] {self.resource}:{self.action}"


class AccessGrant(models.Model):
    """
    The CyberArk-analog artifact: a time-boxed credential/session
    issued after a Policy decision, not the decision itself.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="access_grants")
    granted_by = models.ForeignKey(
        Identity, on_delete=models.SET_NULL, null=True, related_name="grants_issued"
    )
    resource = models.CharField(max_length=128)
    action = models.CharField(max_length=32)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.identity.did} -> {self.resource}:{self.action} ({self.status})"


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="sessions")
    device = models.ForeignKey(
        DeviceBinding, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    session_token = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.is_active and self.expires_at > timezone.now()

    def __str__(self):
        return f"session:{self.identity.did}:{self.created_at:%Y-%m-%d %H:%M}"


class PendingAnchor(models.Model):
    """
    Outbox for ledger writes that failed (ledger down). `manage.py flush_anchors`
    (run continuously by the anchor_worker container) retries them, so audit events
    are delayed, never silently lost.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, related_name="pending_anchors")
    event_type = models.CharField(max_length=32)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"pending {self.event_type} ({self.attempts} attempts)"
