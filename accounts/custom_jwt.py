from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        # Authenticate user
        data = super().validate(attrs)

        user = self.user

        if not user.is_verified:
            raise Exception("Account not verified. Please verify OTP first.")

        # Add extra info in the token response if needed
        data['user_id'] = user.id
        data['email'] = user.email
        data['full_name'] = user.full_name
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
