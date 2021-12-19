from rest_framework import serializers
from stellar_sdk import Account as StellarAccount

from wallet.models import Account


class CredentialSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["address", "balance"]


def account_validator(account):
    try:
        StellarAccount(account=account, sequence=1)
    except ValueError as e:
        raise serializers.ValidationError(str(e))


class PaymentSerializer(serializers.Serializer):
    destination = serializers.CharField(validators=[account_validator])
    amount = serializers.DecimalField(
        max_digits=19, decimal_places=7, min_value=0.0000001, coerce_to_string=False
    )
