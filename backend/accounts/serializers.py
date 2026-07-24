from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import CitizenProfile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this username already exists.",
                code="username_taken",
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        CitizenProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class VerificationCodeSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=16, max_length=256)


class AccountDataSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField(required=False)
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.CharField(required=False)
    identity_verified = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    verified_municipality_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    verified_ward_number = serializers.IntegerField(required=False, allow_null=True)


class AccountResponseSerializer(serializers.Serializer):
    data = AccountDataSerializer()
    meta = serializers.DictField()
    errors = serializers.ListField()


class CsrfDataSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class CsrfResponseSerializer(serializers.Serializer):
    data = CsrfDataSerializer()
    meta = serializers.DictField()
    errors = serializers.ListField()


def serialize_account(user):
    profile, _ = CitizenProfile.objects.get_or_create(user=user)
    return {
        "id": user.pk,
        "username": user.get_username(),
        "email": user.email,
        "role": profile.role,
        "identity_verified": profile.is_identity_verified,
        "is_staff": user.is_staff,
        "verified_municipality_code": profile.verified_municipality_code or None,
        "verified_ward_number": profile.verified_ward_number,
    }
