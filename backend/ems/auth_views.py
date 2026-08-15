from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from datetime import date
from decimal import Decimal
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
import logging
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from employees.models import Employee


User = get_user_model()

logger = logging.getLogger('ems.auth')


def dashboard_url_for(user):
    """Return the permitted dashboard for a user's Django Group role."""
    if user.is_superuser or user.groups.filter(name__in=["Admin", "HR", "Manager"]).exists():
        return "/dashboard/"
    return "/my-dashboard/"


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        roles = list(self.user.groups.values_list("name", flat=True))
        data["roles"] = roles
        data["dashboard_url"] = dashboard_url_for(self.user)
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Thin wrapper to reserve a custom token endpoint for future extensions.

    Currently delegates to SimpleJWT's view but lives here so we can implement
    per-request behavior (remember me) later without changing routes.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        ip = request.META.get('REMOTE_ADDR')
        logger.info('Token obtain attempt for %s from %s', username, ip)
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info('Token obtain success for %s', username)
        else:
            logger.warning('Token obtain failed for %s status=%s detail=%s', username, response.status_code, response.data)
        return response


class RegisterAPIView(APIView):
    """Create a regular employee account. Privileged roles are admin-assigned."""
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        required = ["username", "password", "full_name", "email", "phone", "department", "gender"]
        missing = {field: "This field is required." for field in required if not request.data.get(field)}
        if missing:
            return Response(missing, status=status.HTTP_400_BAD_REQUEST)

        username = request.data["username"].strip()
        email = request.data["email"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            return Response({"username": "This username is already in use."}, status=400)
        if User.objects.filter(email__iexact=email).exists() or Employee.objects.filter(email__iexact=email).exists():
            return Response({"email": "An account with this email already exists."}, status=400)
        if request.data["gender"] not in dict(Employee.GENDER_CHOICES):
            return Response({"gender": "Choose Male or Female."}, status=400)
        try:
            validate_password(request.data["password"])
        except DjangoValidationError as error:
            return Response({"password": list(error.messages)}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=request.data["password"])
            employee_group, _ = Group.objects.get_or_create(name="Employee")
            user.groups.add(employee_group)
            Employee.objects.create(
                employee_id=f"EMP-{user.pk:06d}",
                full_name=request.data["full_name"].strip(),
                email=email,
                phone=request.data["phone"].strip(),
                department=request.data["department"].strip(),
                gender=request.data["gender"],
                salary=Decimal("0.00"),
                joining_date=date.today(),
            )
        logger.info("Employee registration completed for %s", username)
        return Response({"detail": "Registration successful. You can now log in."}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            logger.warning('Logout attempt without refresh token from %s', request.META.get('REMOTE_ADDR'))
            return Response({"detail": "Refresh token required."}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            logger.warning('Logout attempt with invalid refresh token from %s', request.META.get('REMOTE_ADDR'))
            return Response({"detail": "Invalid token."}, status=400)

        return Response({"detail": "Logged out successfully."}, status=200)


class PasswordResetRequestAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"email": "This field is required."}, status=400)
        logger.info('Password reset requested for %s from %s', email, request.META.get('REMOTE_ADDR'))

        form = PasswordResetForm(data={"email": email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                token_generator=default_token_generator,
            )
            return Response({"detail": "Password reset email sent."}, status=200)

        return Response(form.errors, status=400)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, uidb64=None, token=None):
        uid = force_str(urlsafe_base64_decode(uidb64))
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"detail": "Invalid uid."}, status=400)

        if not default_token_generator.check_token(user, token):
            logger.warning('Invalid password reset token for user %s', user.pk)
            return Response({"detail": "Invalid token."}, status=400)

        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"new_password": "This field is required."}, status=400)

        form = SetPasswordForm(user, data={"new_password1": new_password, "new_password2": new_password})
        if form.is_valid():
            form.save()
            logger.info('Password reset completed for user %s', user.pk)
            return Response({"detail": "Password has been set."}, status=200)

        return Response(form.errors, status=400)


class ChangePasswordAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "old_password and new_password are required."}, status=400)

        if not user.check_password(old_password):
            logger.warning('Change password failed for user %s: incorrect old password', user.pk)
            return Response({"detail": "Old password is incorrect."}, status=400)

        user.set_password(new_password)
        user.save()
        logger.info('Password changed for user %s', user.pk)
        return Response({"detail": "Password changed successfully."}, status=200)
