from accounts.models import Membership, User
from accounts.services.auth_service import AuthService
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField()
    number = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_number(self, value):
        if User.objects.filter(number=value).exists():
            raise serializers.ValidationError("Number already exists")
        return value

    def create(self, validated_data):
        return AuthService.register(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            number=validated_data["number"],
        )


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        result = AuthService.login(
            identifier=attrs["identifier"],
            password=attrs["password"],
        )
        if not result:
            raise serializers.ValidationError("Invalid credentials")
        return result


class MembershipBusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="business.id")
    name = serializers.CharField(source="business.name")
    role = serializers.CharField(source="role.code")


class MembershipSerializer(serializers.ModelSerializer):
    business_id = serializers.IntegerField(source="business.id")
    business_name = serializers.CharField(source="business.name")
    role = serializers.CharField(source="role.code")

    class Meta:
        model = Membership
        fields = ("business_id", "business_name", "role")


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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ("name", "number", "avatar")
        extra_kwargs = {
            "name": {"required": False},
            "number": {"required": False, "allow_blank": True},
        }

    def validate_avatar(self, value):
        if value in (None, ""):
            return value
        if not value.startswith(f"uploads/avatars/{self.context['request'].user.pk}/") or ".." in value.split("/"):
            raise serializers.ValidationError("مسیر تصویر پروفایل معتبر نیست.")
        from django.core.files.storage import default_storage
        if not default_storage.exists(value):
            raise serializers.ValidationError("تصویر آپلودشده پیدا نشد.")
        return value

    def update(self, instance, validated_data):
        avatar = validated_data.pop("avatar", serializers.empty)
        old_avatar = instance.avatar.name if instance.avatar else None
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if avatar is not serializers.empty:
            instance.avatar = avatar or None
        instance.save()
        if avatar is not serializers.empty and old_avatar and old_avatar != instance.avatar.name:
            from core.services.UploadService import UploadService
            UploadService.delete(old_avatar)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("رمز عبور فعلی صحیح نیست.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "number", "avatar", "created_at"]
