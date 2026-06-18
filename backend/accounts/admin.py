from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User, Role, Membership, Business, Invitation, RolePermission, Permission


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    ordering = ["id"]

    list_display = (
        "id",
        "email",
        "name",
        "number",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "name",
        "number",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "name",
                    "number",
                    "avatar",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )



@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "slug",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    ordering = (
        "-created_at",
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "business",
        "role",
        "is_active",
    )

    list_filter = (
        "role",
        "is_active",
    )

    autocomplete_fields = (
        "user",
        "business",
        "role",
    )

    search_fields = (
        "user__email",
        "business__name",
    )



@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "code",
        "business",
        "is_system",
    )

    list_filter = (
        "is_system",
    )

    search_fields = (
        "name",
        "code",
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "name",
    )

    search_fields = (
        "code",
        "name",
    )

    ordering = (
        "code",
    )



@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):

    list_display = (
        "role",
        "permission",
    )

    autocomplete_fields = (
        "role",
        "permission",
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):

    list_display = (
        "email",
        "business",
        "role",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
    )