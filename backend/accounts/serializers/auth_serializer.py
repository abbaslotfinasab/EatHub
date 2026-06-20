from accounts.models import Membership
from accounts.services.auth_service import AuthService
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    name = serializers.CharField()
    number = serializers.CharField()

    def validate_email(self, value):
        from accounts.models import User

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")

        return value

    def create(self, validated_data):

        return AuthService.register(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            number=validated_data["number"],
        )


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        result = AuthService.login(
            email=attrs["email"],
            password=attrs["password"],
        )

        if not result:
            raise serializers.ValidationError(
                "Invalid credentials"
            )

        return result



class MembershipBusinessSerializer(serializers.Serializer):

    id = serializers.IntegerField(source="business.id")
    name = serializers.CharField(source="business.name")
    role = serializers.CharField(source="role.code")


class MembershipSerializer(serializers.ModelSerializer):

    business_id = serializers.IntegerField(
        source="business.id"
    )

    business_name = serializers.CharField(
        source="business.name"
    )

    role = serializers.CharField(
        source="role.code"
    )

    class Meta:
        model = Membership

        fields = (
            "business_id",
            "business_name",
            "role",
        )



class LoginResponseSerializer(serializers.Serializer):

    user = serializers.SerializerMethodField()
    memberships = MembershipBusinessSerializer(many=True)

    def get_user(self, obj):
        user = obj["user"]

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }



class ActiveBusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()


class UserMeSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    number = serializers.CharField()

    has_business = serializers.BooleanField()

    memberships = MembershipSerializer(many=True)

    active_business = ActiveBusinessSerializer(
        allow_null=True
    )

    meta = serializers.SerializerMethodField()

    def get_meta(self, obj):
        return obj.get("meta", {})


class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField()
    new_password = serializers.CharField()


