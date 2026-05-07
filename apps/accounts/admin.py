from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User

    list_display = (
        "email",
        "full_name",
        "role",
        "plan",
        "is_active",
        "is_email_verified",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "plan",
        "is_active",
        "is_email_verified",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "full_name",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profil", {"fields": ("full_name", "avatar_url")}),
        ("Rôle et plan", {"fields": ("role", "plan")}),
        ("Statut", {"fields": ("is_active", "is_email_verified")}),
        ("Permissions Django", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "last_login_at", "created_at", "updated_at")}),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "role",
                    "plan",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "is_email_verified",
                ),
            },
        ),
    )