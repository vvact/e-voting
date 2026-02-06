from django.urls import path
from .views import RegisterView, VerifyOTPView, ResendOTPView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name= 'otp'),
    path('resend-otp/', ResendOTPView.as_view(), name= 'ResendOPTView'),
]
