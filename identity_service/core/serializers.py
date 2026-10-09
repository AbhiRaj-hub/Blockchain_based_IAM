from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Identity, DeviceBinding, LedgerAnchor, Policy, AccessGrant, Session

class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ("id", "did", "username", "email", "role", "is_active", "date_joined", "updated_at", "public_key")
        read_only_fields = ("did", "date_joined", "updated_at")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Identity
        fields = ("username", "email", "password", "password_confirm", "role")

    def validate(self, attrs: dict)->dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data: dict)->Identity:
        validated_data.pop("password_confirm")
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

class DeviceBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceBinding
        fields = "__all__"

class LedgerAnchorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAnchor
        fields = "__all__"
        read_only_fields = [f.name for f in LedgerAnchor._meta.fields]

class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = "__all__"

class AccessGrantSerializer(serializers.ModelSerializer):
    identity_name = serializers.ReadOnlyField(source="identity.username")
    policy_name = serializers.ReadOnlyField(source="policy.name")

    class Meta:
        model = AccessGrant
        fields = "__all__"

class AccessCheckSerializer(serializers.Serializer):
    identity_id = serializers.IntegerField()
    resource = serializers.CharField()
    action = serializers.CharField()

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = "__all__"
        read_only_fields = [f.name for f in Session._meta.fields]
