from config.api import success_response
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.serializers import (
    AccountResponseSerializer,
    CsrfResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
    VerificationCodeSerializer,
    serialize_account,
)
from accounts.services import complete_verification


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CsrfResponseSerializer)
    def get(self, request):
        return success_response({"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=AccountResponseSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        request.session.cycle_key()
        return success_response(serialize_account(user), status_code=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses=AccountResponseSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None or not user.is_active:
            raise AuthenticationFailed("The username or password is incorrect.")
        login(request, user)
        request.session.cycle_key()
        return success_response(serialize_account(user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=AccountResponseSerializer)
    def post(self, request):
        logout(request)
        return success_response({"authenticated": False})


class MeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=AccountResponseSerializer)
    def get(self, request):
        if not request.user.is_authenticated:
            return success_response({"authenticated": False})
        return success_response({"authenticated": True, **serialize_account(request.user)})


@method_decorator(csrf_protect, name="dispatch")
class CompleteVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=VerificationCodeSerializer, responses=AccountResponseSerializer)
    def post(self, request):
        serializer = VerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complete_verification(
            user=request.user,
            code=serializer.validated_data["code"],
            request_identifier=request.headers.get("X-Request-ID", ""),
        )
        request.session.cycle_key()
        return success_response(serialize_account(request.user))
