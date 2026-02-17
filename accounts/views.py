from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyOTPSerializer, ResendOTPSerializer
from .models import User, OTP
from django.utils import timezone
from django.contrib.auth import authenticate
import random

# ---------------------------
# REGISTER
# ---------------------------
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate OTP
            code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=code)
            print(f"OTP for {user.email} is {code}")
            return Response({"message": "User registered successfully. Check email for OTP."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# VERIFY OTP
# ---------------------------
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            try:
                user = User.objects.get(email=email)
                otp = OTP.objects.filter(user=user, code=code).latest('created_at')
            except:
                return Response({"error": "Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)

            if otp.is_expired():
                return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.save()
            otp.delete()

            return Response({"message": "Account verified successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# RESEND OTP
# ---------------------------
class ResendOTPView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if user.is_verified:
                return Response({"message": "Account already verified"}, status=status.HTTP_400_BAD_REQUEST)

            OTP.objects.filter(user=user).delete()
            code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=code)
            print(f"NEW OTP for {user.email} is {code}")

            return Response({"message": "New OTP sent"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# LOGIN
# ---------------------------
class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "No account found with this email. Please register."}, status=status.HTTP_404_NOT_FOUND)

        # Authenticate user
        user = authenticate(email=email, password=password)
        if user is None:
            return Response({"detail": "Incorrect password. Please try again."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({"detail": "Account not verified. Please check your email."}, status=status.HTTP_403_FORBIDDEN)

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }, status=status.HTTP_200_OK)


# ---------------------------
# PASSWORD RESET
# ---------------------------
from rest_framework.decorators import api_view

@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    otp = OTP.objects.create(user=user)
    print(f"RESET OTP for {email} is {otp.code}")
    return Response({"message": "OTP sent to email"})


@api_view(['POST'])
def confirm_password_reset(request):
    email = request.data.get("email")
    code = request.data.get("otp")
    new_password = request.data.get("new_password")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    try:
        otp = OTP.objects.filter(user=user, code=code).latest('created_at')
    except OTP.DoesNotExist:
        return Response({"error": "Invalid OTP"}, status=400)

    if otp.is_expired():
        return Response({"error": "OTP expired"}, status=400)

    user.set_password(new_password)
    user.save()
    otp.delete()
    return Response({"message": "Password reset successful"})
