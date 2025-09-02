from rest_framework.serializers import ModelSerializer

from users.models import User, Payment


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'session_id', 'link']
        read_only_fields = ['session_id', 'link']

    def create(self, validated_data):
        return Payment.objects.create(**validated_data)