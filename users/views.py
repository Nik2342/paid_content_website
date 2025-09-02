from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.forms import UserRegisterForm
from users.models import User
from users.serializers import UserSerializer


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")


class UserLoginView(LoginView):
    template_name = "users/login.html"


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        user = User.objects.get(phone=request.data.get("phone"))
        refresh = RefreshToken.for_user(user)

        response.data["tokens"] = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return response
