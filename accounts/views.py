from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from .models import OTP
import random

from .serializers import VerifyOTPSerializer
from .models import User, OTP
from django.utils import timezone

from .serializers import ResendOTPSerializer



class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate OTP
            code = str(random.randint(100000, 999999))

            # Save OTP
            OTP.objects.create(user=user, code=code)

            # TEMP: print OTP in terminal
            print(f"OTP for {user.email} is {code}")

            return Response({
                "message": "User registered successfully. Check email for OTP."
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




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
                return Response(
                    {"error": "Invalid OTP or email"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check expiry
            if otp.is_expired():
                return Response(
                    {"error": "OTP expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify user
            user.is_verified = True
            user.save()

            # Delete OTP after use
            otp.delete()

            return Response(
                {"message": "Account verified successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # If already verified
            if user.is_verified:
                return Response(
                    {"message": "Account already verified"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete old OTPs
            OTP.objects.filter(user=user).delete()

            # Create new OTP
            code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=code)

            print(f"NEW OTP for {user.email} is {code}")

            return Response(
                {"message": "New OTP sent"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
