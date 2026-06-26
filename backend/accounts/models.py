import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q

from accounts.enums import InvitationStatus
from accounts.managers import UserManager
from accounts.utils import generate_english_slug
from core.models import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(
        unique=True
    )

    number = models.CharField(
        max_length=20,
        blank=True,
        unique=True
    )

    name = models.CharField(
        max_length=200
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_staff = models.BooleanField(
        default=False
    )

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return self.email


class Business(BaseModel):
    name = models.CharField(
        max_length=255
    )

    description = models.CharField(
        blank=True,
        null=True
    )

    slug = models.SlugField(
        unique=True
    )

    logo = models.ImageField(
        upload_to="businesses/logos/",
        blank=True,
        null=True
    )

    qr_code = models.ImageField(
        upload_to="businesses/qrcodes/",
        blank=True,
        null=True
    )

    number = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name

    @staticmethod
    def generate_unique_slug(
            instance,
            base_value,
            field_name="slug"
    ):
        base_slug = generate_english_slug(base_value)

        while True:
            slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

            exists = (
                instance.__class__.objects
                .filter(**{field_name: slug})
                .exclude(pk=instance.pk)
                .exists()
            )

            if not exists:
                return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug(self, self.name)

        super().save(*args, **kwargs)


class Role(BaseModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="roles",
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=100
    )

    code = models.CharField(
        max_length=50
    )

    is_system = models.BooleanField(
        default=False
    )

    class Meta:
        unique_together = (
            "business",
            "code"
        )


class Permission(BaseModel):
    name = models.CharField(
        max_length=100
    )

    code = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.name


class RolePermission(BaseModel):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions"
    )

    permission = models.ForeignKey(
        "Permission",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("role", "permission")


class Membership(BaseModel):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    business = models.ForeignKey(
        "Business",
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    role = models.ForeignKey(
        "Role",
        on_delete=models.PROTECT
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="one_active_business_per_user"
            )
        ]




class Invitation(BaseModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="invitations"
    )

    email = models.EmailField()

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="invitations"
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations"
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )

    class Meta:
        unique_together = (
            "business",
            "email",
        )

    def __str__(self):
        return self.email
