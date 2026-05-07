from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "avatar_url",
            "role",
            "plan",
            "is_email_verified",
            "created_at",
        )
        read_only_fields = (
            "id",
            "email",
            "role",
            "plan",
            "is_email_verified",
            "created_at",
        )