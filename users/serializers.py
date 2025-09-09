from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]


class RegisterUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        min_length=3, required=True, trim_whitespace=True
    )
    last_name = serializers.CharField(min_length=3, required=True, trim_whitespace=True)
    email = serializers.EmailField(required=True, trim_whitespace=True)
    password = serializers.CharField(min_length=6)
    username = serializers.CharField(required=True, trim_whitespace=True)


class LoginUserSerializer(serializers.Serializer):
    email = serializers.CharField(required=True, trim_whitespace=True)
    password = serializers.CharField()
