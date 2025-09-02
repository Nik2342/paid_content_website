from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, TemplateView
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from users.forms import UserRegisterForm
from users.models import User, Payment
from users.serializers import UserSerializer, PaymentSerializer
from users.services import create_stripe_price, create_stripe_sessions


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")


class UserLoginView(LoginView):
    template_name = "users/login.html"

@method_decorator(csrf_exempt, name='dispatch')
class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(serializer.validated_data['password'])
        user.save()

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            user = User.objects.get(phone=request.data.get("phone"))
            refresh = RefreshToken.for_user(user)

            return Response({
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user_id": user.id,
                "phone": user.phone
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@method_decorator(csrf_exempt, name='dispatch')
class PaymentCreateAPIView(CreateAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)

        price = create_stripe_price(1000)
        session_id, payment_link = create_stripe_sessions(price)

        payment.session_id = session_id
        payment.link = payment_link
        payment.save()

        self.payment_data = {
            'payment_link': payment_link,
            'session_id': session_id,
            'amount': 1000  # Добавляем сумму для отображения
        }

    def create(self, request, *args, **kwargs):
        # Проверяем, есть ли у пользователя уже активная подписка
        if getattr(request.user, 'has_paid_subscription', False):
            return Response(
                {"error": "У вас уже есть активная подписка"},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.data.update({'amount': 1000})
        response = super().create(request, *args, **kwargs)

        if hasattr(self, 'payment_data'):
            response.data.update(self.payment_data)

        return response

@method_decorator(csrf_exempt, name='dispatch')
class SubscribeView(LoginRequiredMixin, TemplateView):
    template_name = 'subscribe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['amount'] = 1000

        context['has_subscription'] = getattr(self.request.user, 'has_paid_subscription', False)

        return context