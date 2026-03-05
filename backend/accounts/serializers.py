import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "national_id", "password"]

    # ------------------------
    # FULL NAME VALIDATION
    # ------------------------
    def validate_full_name(self, value):
        value = value.strip().upper()  # Remove leading/trailing spaces and uppercase
        value = re.sub(r'\s+', ' ', value)  # Normalize internal spaces

        # Count letters only (ignore spaces/apostrophes)
        letters_only = re.sub(r"[ '\s]+", '', value)
        if len(letters_only) < 4:
            raise serializers.ValidationError(
                "Full name must contain at least 4 letters."
            )

        # Only allow letters, spaces, and apostrophes
        if not re.match(r"^[A-Z\s']+$", value):
            raise serializers.ValidationError(
                "Full name must contain only letters, spaces, and apostrophes."
            )

        return value

    # ------------------------
    # EMAIL VALIDATION
    # ------------------------
    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    # ------------------------
    # NATIONAL ID VALIDATION
    # ------------------------
    def validate_national_id(self, value):
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("National ID must contain digits only.")
        if len(value) < 7 or len(value) > 8:
            raise serializers.ValidationError("National ID must be 7 or 8 digits.")
        if User.objects.filter(national_id=value).exists():
            raise serializers.ValidationError("National ID is already registered.")
        return value

    # ------------------------
    # PASSWORD VALIDATION
    # ------------------------
    def validate_password(self, value):
        value = value.strip()
        if len(value) < 6:
            raise serializers.ValidationError(
                "Password must be at least 6 characters long."
            )
        validate_password(value)  # Django built-in validators
        return value

    # ------------------------
    # CREATE USER
    # ------------------------
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            national_id=validated_data["national_id"],
            full_name=validated_data["full_name"],  # already uppercase, normalized
            password=validated_data["password"],
        )
        return user


# =========================
# VERIFY OTP SERIALIZER
# =========================
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        if len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits.")
        return value


# =========================
# RESEND OTP SERIALIZER
# =========================
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()