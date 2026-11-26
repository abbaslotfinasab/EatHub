from django.core.files.storage import default_storage
from rest_framework import serializers

from accounts.application.user_registration import (
    RegistrationEmailAlreadyExistsError,
    RegistrationNumberAlreadyExistsError,
)
from accounts.composition import list_login_memberships, register_user
from accounts.services.auth_service import AuthService


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField()
    number = serializers.CharField()

    def create(self, validated_data):
        try:
            return register_user().execute(
                email=validated_data["email"],
                password=validated_data["password"],
                name=validated_data["name"],
                number=validated_data["number"],
            )
        except RegistrationEmailAlreadyExistsError:
            raise serializers.ValidationError({"email": "Email already exists"})
        except RegistrationNumberAlreadyExistsError:
            raise serializers.ValidationError({"number": "Number already exists"})


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = AuthService.login(
            identifier=attrs["identifier"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        memberships = list_login_memberships().execute(user_id=user.pk)
        return {"user": user, "memberships": memberships}


class MembershipBusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="business.id")
    name = serializers.CharField(source="business.name")
    role = serializers.CharField(source="role.code")


class MembershipSerializer(serializers.Serializer):
    business_id = serializers.IntegerField()
    business_name = serializers.CharField()
    role = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    memberships = MembershipBusinessSerializer(many=True)

    def get_user(self, obj):
        user = obj["user"]
        return {"id": user.id, "email": user.email, "name": user.name}


class ActiveBusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()
    qr = serializers.URLField(allow_null=True, required=False)
    slug = serializers.CharField()
    logo = serializers.CharField(allow_null=True, required=False)
    permissions = serializers.ListField(child=serializers.CharField())
    inventory_enabled = serializers.BooleanField()


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    number = serializers.CharField(allow_blank=True)
    avatar = serializers.ImageField(allow_null=True, required=False)
    has_business = serializers.BooleanField()
    memberships = MembershipSerializer(many=True)
    active_business = ActiveBusinessSerializer(allow_null=True)
    meta = serializers.SerializerMethodField()

    def get_meta(self, obj):
        return obj.get("meta", {})


class UserProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=200)
    number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    avatar = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_avatar(self, value):
        if value in (None, ""):
            return None
        user_id = self.context["request"].user.pk
        if not value.startswith(f"uploads/avatars/{user_id}/") or ".." in value.split("/"):
            raise serializers.ValidationError("مسیر تصویر پروفایل معتبر نیست.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("تصویر آپلودشده پیدا نشد.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
