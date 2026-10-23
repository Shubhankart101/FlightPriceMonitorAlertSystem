from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import PriceAlert


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username exists")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = ["id", "origin", "destination", "threshold_price", "status", "created_at"]


class AlertCreateSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=10)
    destination = serializers.CharField(max_length=10)
    threshold_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("1"))

    def validate_origin(self, value):
        return value.strip().upper()

    def validate_destination(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError("origin and destination must be different")
        return attrs
