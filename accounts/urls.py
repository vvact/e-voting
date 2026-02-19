from django.urls import path
from .views import RegisterView, VerifyOTPView, ResendOTPView
from .custom_jwt import MyTokenObtainPairView
from .jwt_views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import request_password_reset, confirm_password_reset

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="ResendOPTView"),
    path("login/", CustomTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("password-reset/request/", request_password_reset),
    path("password-reset/confirm/", confirm_password_reset),
]
