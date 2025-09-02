from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import UserCreateAPIView, PaymentCreateAPIView, SubscribeView

app_name = UsersConfig.name

urlpatterns = [
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", TemplateView.as_view(template_name='register.html'), name="register"),
    path('api/register/', UserCreateAPIView.as_view(), name='api_register'),
    path("api/login/", TokenObtainPairView.as_view(), name="api_login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('api/payments/create/', PaymentCreateAPIView.as_view(), name='api_payment_create'),
]
