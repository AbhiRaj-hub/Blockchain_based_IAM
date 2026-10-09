from django.test import TestCase
from ..models import Identity, DeviceBinding, Policy, AccessGrant, Session

class ModelsTestCase(TestCase):
    def test_identity_creation(self)->None:
        user = Identity.objects.create_user(username="testuser", role="user")
        self.assertEqual(user.role, "user")
        self.assertIsNotNone(user.did)
        self.assertTrue("testuser" in str(user))

    def test_device_binding(self)->None:
        user = Identity.objects.create_user(username="testuser")
        dev = DeviceBinding.objects.create(identity=user, device_id="dev-123")
        self.assertTrue("dev-123" in str(dev))

    def test_policy_creation(self)->None:
        p = Policy.objects.create(name="test-policy", resource="data", action="read")
        self.assertEqual(str(p), "test-policy")

    def test_access_grant(self)->None:
        user = Identity.objects.create_user(username="testuser")
        p = Policy.objects.create(name="test-policy", resource="data", action="read")
        g = AccessGrant.objects.create(identity=user, policy=p)
        self.assertTrue("test-policy" in str(g))

    def test_session(self)->None:
        user = Identity.objects.create_user(username="testuser")
        s = Session.objects.create(identity=user, session_token="token123", ip_address="127.0.0.1")
        self.assertTrue("token123" in str(s))
