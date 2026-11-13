from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import MemberRegistrationSerializer,LoginSerializer
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


class MemberRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MemberRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                member = serializer.save()

        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "An account with this email already exists."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "success": True,
                "message": "Member registered successfully.",
                "data": {
                    "id": member.id,
                    "name": member.first_name,
                    "email": member.email
                }
            },
            status=status.HTTP_201_CREATED
        )
    
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        
        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "access": str(refresh.access_token),
                    "member": {
                        "id": user.id,
                        "name": user.first_name,
                        "email": user.email,
                    }
                }
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=int(
                settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
            ),
            path="/api/auth/"
        )

        return response
    

class CurrentMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "success": True,
                "message": "Member details retrieved successfully.",
                "data": {
                    "id": user.id,
                    "name": user.first_name,
                    "email": user.email
                }
            },
            status=status.HTTP_200_OK
        )
        
        

class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token not found."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = TokenRefreshSerializer(
            data={"refresh": refresh_token}
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = serializer.validated_data["access"]
        new_refresh_token = serializer.validated_data.get("refresh")

        response = Response(
            {
                "success": True,
                "message": "Token refreshed successfully.",
                "data": {
                    "access": access_token
                }
            },
            status=status.HTTP_200_OK
        )

        if new_refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=int(
                    settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
                ),
                path="/api/auth/"
            )

        return response
    


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token not found."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {
                "success": True,
                "message": "Logout successful."
            },
            status=status.HTTP_200_OK
        )

        response.delete_cookie(
            key="refresh_token",
            path="/api/auth/",
            samesite="Lax"
        )

        return response