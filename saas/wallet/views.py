from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError
from django.conf import settings
from stellar_sdk import Server, TransactionBuilder, Keypair, Asset
from stellar_sdk.exceptions import NotFoundError

from wallet.serializers import (
    CredentialSerializer,
    AccountSerializer,
    PaymentSerializer,
)


class BearerAuthentication(TokenAuthentication):
    keyword = "Bearer"


user_model = get_user_model()


@api_view(["POST"])
def register(request):
    serializer = CredentialSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user_model.objects.create_user(
                username=serializer.data.get("username"),
                password=serializer.data.get("password"),
            )
            return Response(
                data={"message": "Succesfully created account."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                return Response(
                    data={"message": "Account already exists."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                raise e
        except Exception as e:
            return Response(
                data={"message": "Error registering", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login(request):
    serializer = CredentialSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = authenticate(
                username=serializer.data.get("username"),
                password=serializer.data.get("password"),
            )
            if user is not None:
                token = Token.objects.get(user=user)
                return Response(
                    data={"apikey": token.key},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    data={
                        "message": "Invalid credentials. Either the user name or password is incorrect."
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except Exception as e:
            return Response(
                data={"message": "Error on login", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([BearerAuthentication])
@permission_classes([IsAuthenticated])
def info(request):
    serializer = AccountSerializer(request.user.account)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([BearerAuthentication])
@permission_classes([IsAuthenticated])
def pay(request):
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            if serializer.data.get("amount") > request.user.account.balance:
                return Response(
                    data={"message": "Insufficient account balance."},
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                server = Server(settings.STELLAR_SERVER)
                # Check destination account exists
                destination = server.load_account(serializer.data.get("destination"))

                # Start bulding payment transaction
                vault_keypair = Keypair.from_secret(settings.VAULT_SECRET_KEY)
                vault = server.load_account(vault_keypair.public_key)
                transaction = TransactionBuilder(
                    source_account=vault
                ).append_payment_op(
                    destination=destination.account,
                    amount=serializer.data.get("amount"),
                    asset=Asset.native(),
                    source=request.user.account.address,
                )
                tx = transaction.build()
                tx.sign(vault_keypair)
                server.submit_transaction(tx)

                # If transaction successful, decrease user balance
                request.user.account.balance -= serializer.data.get("amount")
                request.user.account.save()

                return Response(
                    data={"message": "Payment successful."},
                    status=status.HTTP_204_NO_CONTENT,
                )
        except NotFoundError:
            return Response(
                data={"message": "Destination account nout found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                data={"message": "Error registering", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
