from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'national_id', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            national_id=validated_data['national_id'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user



class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
