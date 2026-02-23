from django.contrib import admin
from .models import User, OTP


from django.contrib import admin

# Change admin site titles
admin.site.site_header = "🗳️ E-Voting System Admin"
admin.site.site_title = "E-Voting Admin Portal"
admin.site.index_title = "Welcome to the E-Voting Dashboard"


# =========================
# USER ADMIN
# =========================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "full_name",
        "national_id",
        "is_verified",
        "has_voted",
        "is_staff",
        "created_at",
    )

    search_fields = ("email", "national_id", "full_name")

    list_filter = (
        "is_verified",
        "has_voted",
        "is_staff",
        "is_active",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Personal Info", {"fields": ("email", "full_name", "national_id")}),
        ("Verification", {"fields": ("is_verified", "has_voted")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


# =========================
# OTP ADMIN
# =========================
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "code",
        "created_at",
        "expires_at",
    )

    search_fields = ("user__email",)
    ordering = ("-created_at",)

    readonly_fields = ("code", "created_at", "expires_at")
