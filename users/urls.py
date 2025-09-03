from django.urls import path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import (
    SubscribeView,
    PaymentSuccessView,
    PaymentCancelView,
    UserCreateAPIView,
    PaymentCreateAPIView,
    UserProfileView,
    StripeWebhookView,
)

app_name = "users"

urlpatterns = [
    # HTML pages
    path(
        "login/", TemplateView.as_view(template_name="users/login.html"), name="login"
    ),
    path(
        "logout/",
        TemplateView.as_view(template_name="users/logout.html"),
        name="logout",
    ),
    path(
        "register/",
        TemplateView.as_view(template_name="users/register.html"),
        name="register",
    ),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("payment/success/", PaymentSuccessView.as_view(), name="payment_success"),
    path("payment/cancel/", PaymentCancelView.as_view(), name="payment_cancel"),
    # API endpoints
    path("api/register/", UserCreateAPIView.as_view(), name="api_register"),
    path("api/login/", TokenObtainPairView.as_view(), name="api_login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/user/profile/", UserProfileView.as_view(), name="user_profile"),
    path(
        "api/payments/create/",
        PaymentCreateAPIView.as_view(),
        name="api_payment_create",
    ),
    path("api/stripe/webhook/", StripeWebhookView.as_view(), name="stripe_webhook"),
]
