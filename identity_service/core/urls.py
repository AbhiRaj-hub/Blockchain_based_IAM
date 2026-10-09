from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r"api/identities", views.IdentityViewSet, basename="identity")
router.register(r"api/devices", views.DeviceBindingViewSet, basename="device")
router.register(r"api/policies", views.PolicyViewSet, basename="policy")
router.register(r"api/access/grants", views.AccessGrantViewSet, basename="grant")

urlpatterns = [
    path("api/auth/register/", views.RegisterView.as_view(), name="register"),
    path("api/auth/login/", views.LoginView.as_view(), name="login"),
    path("api/auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/access/check/", views.AccessCheckView.as_view(), name="access_check"),
    path("api/audit/logs/", views.AuditLogView.as_view(), name="audit_logs"),
    path("api/audit/verify/", views.ChainVerifyView.as_view(), name="chain_verify"),
] + router.urls
