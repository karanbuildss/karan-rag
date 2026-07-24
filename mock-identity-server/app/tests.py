import json
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import SimpleTestCase, override_settings


class MockVerificationFlowTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_path = root / "private.pem"
        self.private_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.identities_path = root / "identities.json"
        self.identities_path.write_text(
            json.dumps(
                [
                    {
                        "subject": "mock-test-001",
                        "phone": "9800000001",
                        "citizenship_number": "TEST-PKR-0001",
                        "municipality_code": "PKR",
                        "ward_number": 8,
                    }
                ]
            ),
            encoding="utf-8",
        )
        self.override = override_settings(
            ROOT_URLCONF="app.urls",
            IDENTITY_PRIVATE_KEY_PATH=self.private_path,
            SEEDED_IDENTITIES_PATH=self.identities_path,
            IDENTITY_CLIENT_SECRET="test-client-secret",
            IDENTITY_ISSUER="budget-darpan-mock-id",
            IDENTITY_AUDIENCE="budget-darpan-api",
            IDENTITY_KEY_ID="budget-darpan-test-1",
            IDENTITY_ASSERTION_SECONDS=300,
            IDENTITY_CODE_SECONDS=60,
            IDENTITY_CHALLENGE_SECONDS=300,
            DEMO_OTP="123456",
            EXPOSE_DEMO_OTP=True,
        )
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp_dir.cleanup()

    def test_one_time_code_flow_and_jwks(self):
        start = self.client.post(
            "/api/v1/verification/start/",
            data=json.dumps({"phone": "9800000001", "citizenship_number": "TEST-PKR-0001"}),
            content_type="application/json",
        )
        self.assertEqual(start.status_code, 200)
        challenge_id = start.json()["data"]["challenge_id"]
        self.assertEqual(start.json()["data"]["demo_otp"], "123456")

        confirm = self.client.post(
            "/api/v1/verification/confirm/",
            data=json.dumps({"challenge_id": challenge_id, "otp": "123456"}),
            content_type="application/json",
        )
        self.assertEqual(confirm.status_code, 200)
        code = confirm.json()["data"]["code"]

        exchange = self.client.post(
            "/api/v1/verification/exchange/",
            data=json.dumps({"code": code}),
            content_type="application/json",
            headers={"X-Client-Secret": "test-client-secret"},
        )
        self.assertEqual(exchange.status_code, 200)
        self.assertTrue(exchange.json()["data"]["assertion"])

        reused = self.client.post(
            "/api/v1/verification/exchange/",
            data=json.dumps({"code": code}),
            content_type="application/json",
            headers={"X-Client-Secret": "test-client-secret"},
        )
        self.assertEqual(reused.status_code, 400)
        jwks = self.client.get("/.well-known/jwks.json")
        self.assertEqual(jwks.status_code, 200)
        self.assertEqual(jwks.json()["keys"][0]["alg"], "RS256")

    def test_invalid_identity_and_otp_are_generic(self):
        invalid_identity = self.client.post(
            "/api/v1/verification/start/",
            data=json.dumps({"phone": "no-match", "citizenship_number": "no-match"}),
            content_type="application/json",
        )
        self.assertEqual(invalid_identity.status_code, 400)
        self.assertNotIn("phone", str(invalid_identity.json()).lower())
