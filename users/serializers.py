from rest_framework.serializers import ModelSerializer

from users.models import User, Payment


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "user", "session_id", "link"]  # Убираем amount совсем
        read_only_fields = ["id", "user", "session_id", "link"]

    def create(self, validated_data):
        # Создаем объект payment вручную
        payment = Payment.objects.create(
            user=self.context["request"].user,
            amount=1000,  # Фиксированное значение
            session_id=validated_data.get("session_id", ""),
            link=validated_data.get("link", ""),
        )
        return payment
