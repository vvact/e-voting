import re
import random
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password


# =========================
# USER MANAGER
# =========================
class UserManager(BaseUserManager):
    def create_user(self, email, national_id, full_name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not national_id:
            raise ValueError("Users must have a National ID")
        if not full_name:
            raise ValueError("Users must have a full name")

        # Normalize inputs
        email = self.normalize_email(email).strip()
        national_id = national_id.strip()
        full_name = full_name.strip().upper()
        full_name = re.sub(r'\s+', ' ', full_name)  # normalize spaces

        if not national_id.isdigit():
            raise ValueError("National ID must contain digits only.")
        if len(national_id) < 7 or len(national_id) > 8:
            raise ValueError("National ID must be 7 or 8 digits.")

        # Validate full_name letters
        letters_only = re.sub(r"[ '\s]+", '', full_name)
        if len(letters_only) < 4:
            raise ValueError("Full name must contain at least 4 letters.")
        if not re.match(r"^[A-Z\s']+$", full_name):
            raise ValueError("Full name must contain only letters, spaces, and apostrophes.")

        user = self.model(
            email=email,
            national_id=national_id,
            full_name=full_name,
        )

        user.set_password(password)
        user.full_clean()  # enforce model validation
        user.save(using=self._db)
        return user

    def create_superuser(self, email, national_id, full_name, password):
        user = self.create_user(
            email=email,
            national_id=national_id,
            full_name=full_name,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_verified = True
        user.save(using=self._db)
        return user


# =========================
# USER MODEL
# =========================
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)

    national_id = models.CharField(
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{7,8}$',
                message="National ID must be 7 to 8 digits only.",
            )
        ],
    )

    full_name = models.CharField(max_length=255)

    is_verified = models.BooleanField(default=False)
    has_voted = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["national_id", "full_name"]

    # ---------------------------
    # VALIDATION
    # ---------------------------
    def clean(self):
        # Normalize national ID
        if self.national_id:
            self.national_id = self.national_id.strip()
            if not self.national_id.isdigit():
                raise ValidationError("National ID must contain digits only.")
            if len(self.national_id) < 7 or len(self.national_id) > 8:
                raise ValidationError("National ID must be 7 or 8 digits.")

        # Normalize full name: uppercase, uniform spacing, allow apostrophes
        if self.full_name:
            self.full_name = self.full_name.strip().upper()
            self.full_name = re.sub(r'\s+', ' ', self.full_name)

            # Count letters only (ignore spaces/apostrophes)
            letters_only = re.sub(r"[ '\s]+", '', self.full_name)
            if len(letters_only) < 4:
                raise ValidationError("Full name must contain at least 4 letters.")

            if not re.match(r"^[A-Z\s']+$", self.full_name):
                raise ValidationError(
                    "Full name must contain only letters, spaces, and apostrophes."
                )

    # ---------------------------
    # SAVE
    # ---------------------------
    def save(self, *args, **kwargs):
        self.full_clean()  # always validate before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


# =========================
# OTP MODEL (Improved & Secure)
# =========================
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=128)  # hashed OTP
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            raw_code = str(random.randint(100000, 999999))
            self.code = make_password(raw_code)
            self._raw_code = raw_code  # temporary access for sending SMS/email

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)

        super().save(*args, **kwargs)

    def verify(self, input_code):
        return check_password(input_code, self.code)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email}"