import logging
import uuid
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Identity, DeviceBinding, LedgerAnchor, Policy, AccessGrant, Session
from .serializers import (
    IdentitySerializer, RegisterSerializer, DeviceBindingSerializer,
    PolicySerializer, AccessGrantSerializer, AccessCheckSerializer
)
from .permissions import IsAdmin, IsAdminOrAuditor, IsOwnerOrAdmin
from .services import ledger_client, policy_engine

logger = logging.getLogger(__name__)

class RegisterView(CreateAPIView):
    queryset = Identity.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer)->None:
        identity = serializer.save()
        try:
            res = ledger_client.post_event(
                event_type="identity_registered",
                payload={"did": str(identity.did), "username": identity.username, "role": identity.role}
            )
            if res and "index" in res:
                LedgerAnchor.objects.create(
                    identity=identity,
                    block_index=res["index"],
                    block_hash=res.get("hash", ""),
                    event_type="identity_registered"
                )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request)->Response:
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = Identity.objects.filter(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                return Response({"error": "User inactive"}, status=status.HTTP_400_BAD_REQUEST)
            
            refresh = RefreshToken.for_user(user)
            
            session = Session.objects.create(
                identity=user,
                session_token=str(refresh.access_token),
                ip_address=request.META.get("REMOTE_ADDR", "127.0.0.1"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")
            )
            
            try:
                ledger_client.post_event(
                    event_type="identity_login",
                    payload={"did": str(user.did), "session_id": session.id}
                )
            except Exception as e:
                logger.warning(f"Ledger failed: {e}")
                
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request)->Response:
        session_token = request.auth
        if session_token:
            Session.objects.filter(session_token=str(session_token)).update(
                is_active=False, ended_at=timezone.now()
            )
            try:
                ledger_client.post_event(
                    event_type="identity_logout",
                    payload={"did": str(request.user.did)}
                )
            except Exception as e:
                logger.warning(f"Ledger failed: {e}")
        return Response(status=status.HTTP_200_OK)

class IdentityViewSet(viewsets.ModelViewSet):
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer

    def get_permissions(self)->list:
        if self.action in ["list", "destroy"]:
            return [IsAdmin()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self)->list:
        if self.request.user.role == "admin":
            return Identity.objects.all()
        return Identity.objects.filter(id=self.request.user.id)
        
    def perform_update(self, serializer)->None:
        identity = serializer.save()
        try:
            ledger_client.post_event(
                event_type="identity_updated",
                payload={"did": str(identity.did)}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

class DeviceBindingViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceBindingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self)->list:
        if self.request.user.role == "admin":
            return DeviceBinding.objects.all()
        return DeviceBinding.objects.filter(identity=self.request.user)

    def perform_create(self, serializer)->None:
        binding = serializer.save(identity=self.request.user)
        try:
            ledger_client.post_event(
                event_type="device_bound",
                payload={"did": str(binding.identity.did), "device_id": binding.device_id}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

class PolicyViewSet(viewsets.ModelViewSet):
    queryset = Policy.objects.all()
    serializer_class = PolicySerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer)->None:
        policy = serializer.save(created_by=self.request.user)
        try:
            ledger_client.post_event(
                event_type="policy_created",
                payload={"policy_id": policy.id, "name": policy.name}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

    def perform_update(self, serializer)->None:
        policy = serializer.save()
        try:
            ledger_client.post_event(
                event_type="policy_updated",
                payload={"policy_id": policy.id, "name": policy.name}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

class AccessGrantViewSet(viewsets.ModelViewSet):
    serializer_class = AccessGrantSerializer

    def get_permissions(self)->list:
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self)->list:
        if self.request.user.role == "admin":
            return AccessGrant.objects.all()
        return AccessGrant.objects.filter(identity=self.request.user)

    def perform_create(self, serializer)->None:
        grant = serializer.save(granted_by=self.request.user)
        try:
            ledger_client.post_event(
                event_type="access_granted",
                payload={"did": str(grant.identity.did), "policy_id": grant.policy.id}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")

    def perform_destroy(self, instance)->None:
        try:
            ledger_client.post_event(
                event_type="access_revoked",
                payload={"did": str(instance.identity.did), "policy_id": instance.policy.id}
            )
        except Exception as e:
            logger.warning(f"Ledger failed: {e}")
        instance.delete()

class AccessCheckView(APIView):
    def post(self, request)->Response:
        serializer = AccessCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        identity = Identity.objects.filter(id=data["identity_id"]).first()
        if not identity:
            return Response({"error": "Identity not found"}, status=status.HTTP_404_NOT_FOUND)
            
        result = policy_engine.evaluate_access(identity, data["resource"], data["action"])
        return Response(result)

class AuditLogView(APIView):
    permission_classes = [IsAdminOrAuditor]

    def get(self, request)->Response:
        page = request.query_params.get("page", 1)
        size = request.query_params.get("size", 20)
        try:
            data = ledger_client.get_blocks(page=page, page_size=size)
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChainVerifyView(APIView):
    permission_classes = [IsAdminOrAuditor]

    def get(self, request)->Response:
        try:
            data = ledger_client.verify_chain()
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
