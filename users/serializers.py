from rest_framework.serializers import ModelSerializer

from users.models import User, Payment


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class PaymentCreateSerializer(ModelSerializer):
    """Сериализатор только для создания платежей"""

    class Meta:
        model = Payment
        fields = []  # Пустой список полей - ничего не требуется от пользователя

    def create(self, validated_data):
        # Создаем объект payment вручную
        request = self.context["request"]
        amount = 1000  # Фиксированная сумма

        # Создаем платежную сессию
        from users.services import create_payment_session

        session_id, payment_link = create_payment_session(amount, "Премиум подписка")

        payment = Payment.objects.create(
            user=request.user, amount=amount, session_id=session_id, link=payment_link
        )

        # Сохраняем данные для response
        self.payment_data = {
            "payment_link": payment_link,
            "session_id": session_id,
            "amount": amount,
        }

        return payment
