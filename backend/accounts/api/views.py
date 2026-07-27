from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.api.serializers import LoginSerializer, SignupSerializer, UserSerializer


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

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


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
