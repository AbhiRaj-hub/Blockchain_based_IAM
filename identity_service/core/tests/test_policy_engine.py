from django.test import TestCase
from ..models import Identity, Policy, AccessGrant
from ..services.policy_engine import evaluate_access

class PolicyEngineTestCase(TestCase):
    def setUp(self)->None:
        self.user = Identity.objects.create_user(username="testuser", role="user")
        self.admin = Identity.objects.create_user(username="adminuser", role="admin")

    def test_default_deny(self)->None:
        res = evaluate_access(self.user, "secret", "read")
        self.assertFalse(res["allowed"])

    def test_allow_policy(self)->None:
        p = Policy.objects.create(name="allow-read", resource="secret", action="read", effect="allow")
        AccessGrant.objects.create(identity=self.user, policy=p)
        res = evaluate_access(self.user, "secret", "read")
        self.assertTrue(res["allowed"])
        self.assertIn("allow-read", res["matched_policies"])

    def test_deny_overrides_allow(self)->None:
        p1 = Policy.objects.create(name="allow-read", resource="secret", action="read", effect="allow")
        p2 = Policy.objects.create(name="deny-read", resource="secret", action="read", effect="deny")
        AccessGrant.objects.create(identity=self.user, policy=p1)
        AccessGrant.objects.create(identity=self.user, policy=p2)
        res = evaluate_access(self.user, "secret", "read")
        self.assertFalse(res["allowed"])
        self.assertIn("deny-read", res["matched_policies"])

    def test_abac_conditions(self)->None:
        p = Policy.objects.create(
            name="allow-admin-only",
            resource="secret",
            action="read",
            effect="allow",
            conditions={"role": ["admin"]}
        )
        AccessGrant.objects.create(identity=self.user, policy=p)
        AccessGrant.objects.create(identity=self.admin, policy=p)
        
        res1 = evaluate_access(self.user, "secret", "read")
        self.assertFalse(res1["allowed"])
        
        res2 = evaluate_access(self.admin, "secret", "read")
        self.assertTrue(res2["allowed"])
