from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View


class LoginPageView(View):
    def get(self, request):
        return render(request, "ems/login.html")


class RegisterPageView(View):
    def get(self, request):
        return render(request, "ems/register.html")


class HomePageView(View):
    def get(self, request):
        return redirect("login")


class PasswordResetPageView(View):
    def get(self, request):
        return render(request, "ems/password_reset.html")


class PasswordResetConfirmPageView(View):
    def get(self, request, uidb64=None, token=None):
        return render(request, "ems/password_reset_confirm.html", {"uidb64": uidb64, "token": token})


class ChangePasswordPageView(View):
    def get(self, request):
        return render(request, "ems/change_password.html")


class DashboardPageView(View):
    def get(self, request):
        return render(request, "ems/dashboard.html")


class EmployeeDashboardPageView(View):
    def get(self, request):
        return render(request, "ems/dashboard.html", {"employee_dashboard": True})
