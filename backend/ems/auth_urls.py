from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .auth_views import (
    CustomTokenObtainPairView,
    LogoutView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,
    ChangePasswordAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='token_logout'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
]
