from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.utils import timezone  # 🔥 import timezone

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        if not user.is_verified:
            raise serializers.ValidationError("Account not verified. Verify OTP first.")

        # 🔥 UPDATE LAST LOGIN HERE
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        data.update({
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name
        })

        return data

