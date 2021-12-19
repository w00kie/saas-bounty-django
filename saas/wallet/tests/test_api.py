from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal


class RegisterTests(APITestCase):
    """Test register endpoint."""

    def test_successful(self):
        """Successful registration."""
        response = self.client.post(
            "/register",
            {"username": "bob", "password": "notagoodpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_malformed(self):
        """Malformed registration."""
        response = self.client.post(
            "/register",
            {"username": "bob", "foo": "bar"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unique(self):
        """Username already registered."""
        user_model = get_user_model()
        user_model.objects.create_user(username="bob", password="anotherpassword")
        # Try registering the same username
        response = self.client.post(
            "/register",
            {"username": "bob", "password": "notagoodpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class LoginTests(APITestCase):
    """Test login endpoint."""

    def test_successful(self):
        """Successful registration."""
        user_model = get_user_model()
        user_model.objects.create_user(username="bob", password="notagoodpassword")
        response = self.client.post(
            "/login",
            {"username": "bob", "password": "notagoodpassword"},
            format="json",
        )
        self.assertContains(
            response=response, text="apikey", status_code=status.HTTP_200_OK
        )

    def test_no_user(self):
        """User not found."""
        response = self.client.post(
            "/login",
            {"username": "bob", "password": "notagoodpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed(self):
        """Malformed login."""
        response = self.client.post(
            "/login",
            {"username": "bob", "foo": "bar"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InfoTests(APITestCase):
    """Test info endpoint."""

    def test_successful(self):
        """Successful call to info."""
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="bob", password="notagoodpassword"
        )
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        response = self.client.get("/info")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            response.content, {"address": user.account.address, "balance": "0.0000000"}
        )

    def test_unauthorized(self):
        """Unauthorized call."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer 0123456789")

        response = self.client.get("/info")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PayTests(APITestCase):
    """Test pay endpoint."""

    def test_successfull(self):
        """Balance is insufficient."""
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="bob", password="notagoodpassword"
        )
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        # Add a balance to the user's account
        user.account.balance = "100"
        user.account.save()

        response = self.client.post(
            "/pay",
            {
                "destination": "GCR5GH7NATSLBGYUX5HKONBR5JSVIOEWKOOSOEI2NMOG2NRJSYZGNRL2",
                "amount": "0.001",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user.refresh_from_db()
        self.assertEqual(Decimal("99.999"), user.account.balance)

    def test_insufficient_balance(self):
        """Balance is insufficient."""
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="bob", password="notagoodpassword"
        )
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        response = self.client.post(
            "/pay",
            {
                "destination": "GBLKRATZODTSJNU7XTB5HY5VAAN63CPRT77UYZT2VLCNXE7F3YHSW22M",
                "amount": "200.20",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_not_found(self):
        """Destination not found."""
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="bob", password="notagoodpassword"
        )
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        # Add a balance to the user's account
        user.account.balance = "10000"
        user.account.save()

        response = self.client.post(
            "/pay",
            {
                "destination": "GBLKRATZODTSJNU7XTB5HY5VAAN63CPRT77UYZT2VLCNXE7F3YHSW22M",
                "amount": "200.20",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_malformed(self):
        """Malformed payloads."""
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="bob", password="notagoodpassword"
        )
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

        # Bad Stellar account
        response = self.client.post(
            "/pay",
            {
                "destination": "FOOBAR",
                "amount": "200.20",
            },
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg="Bad Stellar account"
        )

        # Bad amount
        response = self.client.post(
            "/pay",
            {
                "destination": "GBLKRATZODTSJNU7XTB5HY5VAAN63CPRT77UYZT2VLCNXE7F3YHSW22M",
                "amount": "-30",
            },
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg="Bad amount"
        )

    def test_unauthorized(self):
        """Unauthorized call."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer 0123456789")

        response = self.client.post(
            "/pay",
            {
                "destination": "GBLKRATZODTSJNU7XTB5HY5VAAN63CPRT77UYZT2VLCNXE7F3YHSW22M",
                "amount": "200.20",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
