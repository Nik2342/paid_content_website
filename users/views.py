from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, TemplateView
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
import stripe
from django.conf import settings

from users.forms import UserRegisterForm
from users.models import User, Payment
from users.serializers import UserSerializer, PaymentSerializer
from users.services import create_payment_session


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")


class UserLoginView(LoginView):
    template_name = "users/login.html"


@method_decorator(csrf_exempt, name="dispatch")
class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(serializer.validated_data["password"])
        user.save()

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            user = User.objects.get(phone=request.data.get("phone"))
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    "user_id": user.id,
                    "phone": user.phone,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentCreateAPIView(CreateAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.has_paid_subscription:
            raise ValidationError("У вас уже есть активная подписка")

        amount = 1000

        try:
            session_id, payment_link = create_payment_session(
                amount, "Премиум подписка"
            )

            # Передаем только те данные, которые нужны сериализатору
            serializer.save(session_id=session_id, link=payment_link)

            self.payment_data = {
                "payment_link": payment_link,
                "session_id": session_id,
                "amount": amount,
            }

        except Exception as e:
            raise ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        try:
            # Просто вызываем родительский метод
            response = super().create(request, *args, **kwargs)
            if hasattr(self, "payment_data"):
                response.data.update(self.payment_data)
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class SubscribeView(LoginRequiredMixin, TemplateView):
    template_name = "subscribe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["amount"] = 1000
        context["has_subscription"] = getattr(
            self.request.user, "has_paid_subscription", False
        )
        return context


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """Обработчик вебхуков от Stripe для обновления статуса подписки"""

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return JsonResponse({"error": "Invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({"error": "Invalid signature"}, status=400)

        # Обрабатываем успешный платеж
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            try:
                # Находим платеж по session_id
                payment = Payment.objects.get(session_id=session.id)

                # Активируем подписку пользователя
                payment.user.has_paid_subscription = True
                payment.user.save()

                # Можно также обновить статус платежа
                # payment.status = 'completed'
                # payment.save()

            except Payment.DoesNotExist:
                # Логируем ошибку, но не прерываем выполнение
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Payment with session_id {session.id} not found")

        return JsonResponse({"status": "success"})


class UserProfileView(APIView):
    """API для получения информации о текущем пользователе"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "phone": request.user.phone,
                "email": request.user.email,
                "has_paid_subscription": request.user.has_paid_subscription,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
            }
        )


class PaymentSuccessView(TemplateView):
    """Страница успешной оплаты"""

    template_name = "payment_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Можно добавить дополнительную логику, например, проверку сессии
        return context


class PaymentCancelView(TemplateView):
    """Страница отмены оплаты"""

    template_name = "payment_cancel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "Оплата была отменена. Вы можете попробовать снова."
        return context
