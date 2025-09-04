from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, TemplateView
from rest_framework import status
from rest_framework.decorators import api_view
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
from users.serializers import UserSerializer, PaymentCreateSerializer
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



@api_view(['POST'])
def api_django_login(request):
    """Создание Django сессии после JWT аутентификации"""
    try:
        # Простая проверка - если запрос пришел, значит JWT валиден
        # (JWT аутентификация уже прошла через permission_classes)
        login(request, request.user)
        return Response({'status': 'django_session_created'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentCreateAPIView(APIView):  # Используем APIView вместо CreateAPIView
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Проверяем, есть ли уже активная подписка
        if request.user.has_paid_subscription:
            return Response(
                {"error": "У вас уже есть активная подписка"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = 1000  # Фиксированная сумма

        try:
            # Создаем платежную сессию
            session_id, payment_link = create_payment_session(
                amount, "Премиум подписка"
            )

            # Создаем запись о платеже
            payment = Payment.objects.create(
                user=request.user,
                amount=amount,
                session_id=session_id,
                link=payment_link,
            )

            return Response(
                {
                    "payment_link": payment_link,
                    "session_id": session_id,
                    "amount": amount,
                    "payment_id": payment.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class SubscribeView(TemplateView):
    template_name = "subscribe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["amount"] = 1000

        # Проверяем параметры URL после возврата от Stripe
        session_id = self.request.GET.get("session_id")
        success = self.request.GET.get("success")

        if success and session_id:
            # Активируем подписку при возврате с успешной оплатой
            context["activation_result"] = self.activate_subscription(session_id)

        return context

    def activate_subscription(self, session_id):
        try:
            # Проверяем статус платежа в Stripe
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                # Находим платеж по session_id
                try:
                    payment = Payment.objects.get(session_id=session_id)
                except Payment.DoesNotExist:
                    # Если платеж не найден, создаем новый
                    user = self.find_user_from_session(session)
                    if user:
                        payment = Payment.objects.create(
                            user=user,
                            amount=session.amount_total / 100,
                            session_id=session_id,
                            link=session.url,
                            status="completed",
                        )
                    else:
                        return "user_not_found"

                # Активируем подписку
                payment.user.has_paid_subscription = True
                payment.user.save()

                # Обновляем статус платежа
                payment.status = "completed"
                payment.save()

                return "success"
            else:
                return "payment_not_completed"

        except stripe.error.StripeError as e:
            return f"stripe_error: {str(e)}"
        except Exception as e:
            return f"error: {str(e)}"

    def find_user_from_session(self, session):
        # Пытаемся найти пользователя по email из сессии
        if session.customer_email:
            try:
                return User.objects.get(email=session.customer_email)
            except User.DoesNotExist:
                pass

        # Или по последнему платежу (если пользователь был аутентифицирован)
        try:
            return Payment.objects.filter(session_id=session.id).first().user
        except:
            return None


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


@method_decorator(csrf_exempt, name="dispatch")
class ActivateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Проверяем статус платежа в Stripe
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                # Активируем подписку
                request.user.has_paid_subscription = True
                request.user.save()

                # Сохраняем информацию о платеже
                Payment.objects.create(
                    user=request.user,
                    amount=session.amount_total / 100,  # Конвертируем из копеек
                    session_id=session_id,
                    link=session.url,
                    status="completed",
                )

                return Response({"status": "subscription_activated"})
            else:
                return Response(
                    {"error": "Payment not completed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )
