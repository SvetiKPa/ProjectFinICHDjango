import re
from typing import Any
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
# from apps.booking.enums import Role
from apps.booking.models import User



class UserListSerializer(serializers.ModelSerializer):
    posts_cnt = serializers.IntegerField(
        required=False
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'posts_cnt'
        ]

    def to_representation(self, instance: User):
        representation = super().to_representation(instance)

        if self.context.get('include_related'):
            representation['reviews'] = [
                {
                    "id": review.id,
                    "rating": review.rating,
                    "description": review.description,
                }
                for review in instance.reviews.all()
            ]

        return representation


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = [
            'password',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True
    )
    re_password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'password',
            're_password',
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        first_name = attrs.get('first_name')
        last_name = attrs.get('last_name')
        password = attrs.get('password')
        re_password = attrs.pop('re_password', None)

        re_pattern = r"^[a-zA-Z]+$"

        if not re.match(re_pattern, first_name):
            raise serializers.ValidationError(
                {
                    "first_name": "Должно состоять только из латиницы"
                }
            )

        if not re.match(re_pattern, last_name):
            raise serializers.ValidationError(
                {
                    "last_name": "Должно состоять только из латиницы"
                }
            )

        if not password:
            raise serializers.ValidationError(
                {
                    "password": "Это поле обязательно к заполнению"
                }
            )

        if not re_password:
            raise serializers.ValidationError(
                {
                    "re_password": "Это поле обязательно к заполнению"
                }
            )

        validate_password(password)

        if password != re_password:
            raise serializers.ValidationError(
                {
                    "re_password": "Пароли должны совпадать"
                }
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop('password')
        # role = validated_data.get('role')

        user = User(**validated_data)
        user.set_password(password)

        user.save()

        return user
