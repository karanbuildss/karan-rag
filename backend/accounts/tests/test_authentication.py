from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import CitizenProfile
from accounts.services import _exchange_code

User = get_user_model()


class SessionAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_token(self):
        response = self.client.get(reverse("auth-csrf"))
        return response.data["data"]["csrf_token"]

    def test_registration_requires_csrf_and_creates_server_session(self):
        payload = {
            "username": "citizen-one",
            "email": "citizen@example.test",
            "password": "safe-demo-password-123",
        }
        denied = self.client.post(reverse("auth-register"), payload, format="json")
        self.assertEqual(denied.status_code, 403)

        token = self.csrf_token()
        response = self.client.post(
            reverse("auth-register"),
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["role"], "citizen")
        self.assertIn("sessionid", self.client.cookies)

        me = self.client.get(reverse("auth-me"))
        self.assertTrue(me.data["data"]["authenticated"])

    def test_login_rejects_invalid_credentials(self):
        User.objects.create_user(username="citizen", password="safe-demo-password-123")
        token = self.csrf_token()
        response = self.client.post(
            reverse("auth-login"),
            {"username": "citizen", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 403)


@override_settings(
    CITIZEN_HASH_SECRET="test-citizen-hmac-secret",
    MOCK_IDENTITY_ISSUER="budget-darpan-mock-id",
    MOCK_IDENTITY_AUDIENCE="budget-darpan-api",
)
class IdentityVerificationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private_pem = cls.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cls.public_pem = cls.private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def setUp(self):
        self.user = User.objects.create_user(
            username="verify-me",
            password="safe-demo-password-123",
        )
        self.client = APIClient()
        self.client.force_login(self.user)

    @override_settings(
        MOCK_IDENTITY_SERVER_URL="http://identity.test",
        MOCK_IDENTITY_CLIENT_SECRET="test-client-secret",
    )
    @patch("accounts.services.urlopen")
    def test_exchange_reads_mock_service_response_envelope(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b'{"data":{"assertion":"signed-value"}}'

        self.assertEqual(_exchange_code("one-time-code"), "signed-value")

    def assertion(self, *, expired=False):
        now = datetime.now(UTC)
        expires = now - timedelta(seconds=1) if expired else now + timedelta(minutes=5)
        return jwt.encode(
            {
                "iss": "budget-darpan-mock-id",
                "aud": "budget-darpan-api",
                "sub": "mock-government-identity-001",
                "jti": f"test-jti-{expired}",
                "phone_verified": True,
                "citizenship_verified": True,
                "municipality_code": "PKR",
                "ward_number": 8,
                "iat": int(now.timestamp()),
                "exp": int(expires.timestamp()),
            },
            self.private_pem,
            algorithm="RS256",
        )

    @patch("accounts.services._public_key")
    @patch("accounts.services._exchange_code")
    def test_signed_assertion_upgrades_account_without_identity_values(self, exchange, public_key):
        exchange.return_value = self.assertion()
        public_key.return_value = self.public_pem

        response = self.client.post(
            reverse("verification-complete"),
            {"code": "a" * 24},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        profile = CitizenProfile.objects.get(user=self.user)
        self.assertEqual(profile.role, CitizenProfile.Role.VERIFIED_CITIZEN)
        self.assertEqual(profile.verified_municipality_code, "PKR")
        self.assertEqual(profile.verified_ward_number, 8)
        self.assertEqual(len(profile.citizen_key), 64)
        self.assertNotIn("citizenship", response.data["data"])
        self.assertNotIn("phone", response.data["data"])

    @patch("accounts.services._public_key")
    @patch("accounts.services._exchange_code")
    def test_verification_does_not_downgrade_an_elevated_role(self, exchange, public_key):
        CitizenProfile.objects.create(user=self.user, role=CitizenProfile.Role.OFFICIAL)
        exchange.return_value = self.assertion()
        public_key.return_value = self.public_pem

        response = self.client.post(
            reverse("verification-complete"),
            {"code": "c" * 24},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], CitizenProfile.Role.OFFICIAL)

    @patch("accounts.services._public_key")
    @patch("accounts.services._exchange_code")
    def test_expired_assertion_is_rejected(self, exchange, public_key):
        exchange.return_value = self.assertion(expired=True)
        public_key.return_value = self.public_pem
        response = self.client.post(
            reverse("verification-complete"),
            {"code": "b" * 24},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(CitizenProfile.objects.filter(user=self.user).exists())
