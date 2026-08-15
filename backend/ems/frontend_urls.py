from django.urls import path
from .frontend_views import (
    HomePageView,
    LoginPageView,
    RegisterPageView,
    PasswordResetPageView,
    PasswordResetConfirmPageView,
    ChangePasswordPageView,
    DashboardPageView,
    EmployeeDashboardPageView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("register/", RegisterPageView.as_view(), name="register"),
    path("password-reset/", PasswordResetPageView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/<str:uidb64>/<str:token>/",
        PasswordResetConfirmPageView.as_view(),
        name="password_reset_confirm",
    ),
    path("change-password/", ChangePasswordPageView.as_view(), name="change_password"),
    path("dashboard/", DashboardPageView.as_view(), name="dashboard"),
    path("my-dashboard/", EmployeeDashboardPageView.as_view(), name="employee_dashboard"),
]
