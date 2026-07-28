from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.api.serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    SignupSerializer,
    UserSerializer,
)
from accounts.google import GoogleTokenError, verify_google_id_token
from accounts.models import User


def set_auth_cookies(response, access, refresh):
    common = {
        "httponly": settings.AUTH_COOKIE_HTTPONLY,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": settings.AUTH_COOKIE_PATH,
    }
    response.set_cookie(settings.AUTH_COOKIE_ACCESS, str(access), **common)
    response.set_cookie(settings.AUTH_COOKIE_REFRESH, str(refresh), **common)


def clear_auth_cookies(response):
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path=settings.AUTH_COOKIE_PATH)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path=settings.AUTH_COOKIE_PATH)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": UserSerializer(user).data}, status=status.HTTP_200_OK
        )
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not raw_refresh:
            return Response(
                {"detail": "No refresh token."}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access = refresh.access_token
        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
            if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION"):
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

        response = Response(status=status.HTTP_200_OK)
        set_auth_cookies(response, access, refresh)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except (TokenError, AttributeError):
                pass
        response = Response(status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": UserSerializer(user, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return Response(UserSerializer(user, context={"request": request}).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response(
                {"detail": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            claims = verify_google_id_token(token)
        except GoogleTokenError:
            return Response(
                {"detail": "Invalid Google token."}, status=status.HTTP_401_UNAUTHORIZED
            )
        if not claims.get("email_verified"):
            return Response(
                {"detail": "Google email is not verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = self._get_or_create(claims)
        refresh = RefreshToken.for_user(user)
        response = Response(
            {"user": UserSerializer(user, context={"request": request}).data},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, refresh.access_token, refresh)
        return response

    def _get_or_create(self, claims):
        sub = claims["sub"]
        email = claims["email"]

        user = User.objects.filter(google_sub=sub).first()
        if user:
            return user

        user = User.objects.filter(email__iexact=email).first()
        if user:
            if not user.google_sub:
                user.google_sub = sub
                user.save(update_fields=["google_sub"])
            return user

        return User.objects.create_user(
            email=email,
            full_name=claims.get("name", ""),
            password=None,
            google_sub=sub,
            avatar_url=claims.get("picture"),
            privacy_accepted_at=timezone.now(),
        )
