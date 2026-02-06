from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import random


class UserManager(BaseUserManager):
    def create_user(self, email, national_id, full_name, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        if not national_id:
            raise ValueError("Users must have a National ID")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            national_id=national_id,
            full_name=full_name,
        )

        user.set_password(password)
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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    national_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)

    is_verified = models.BooleanField(default=False)
    has_voted = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['national_id', 'full_name']

    def __str__(self):
        return self.email


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(random.randint(100000, 999999))

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=60)

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at
