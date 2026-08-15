# WorkSphereAI Backend

This repository contains the Django REST Framework backend for WorkSphereAI.

## Local setup

1. Create and activate a virtual environment:

```powershell
python -m venv venv
& .\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Create and configure environment variables:

Copy the example file and edit it before running the app:

```powershell
copy .env.example .env
```

Then update `.env` with secure values, especially `SECRET_KEY`.

A secure secret key should be at least 32 characters long. For example:

```powershell
$env:SECRET_KEY = 'a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4'
```

4. Run migrations:

```powershell
python manage.py migrate
```

5. Run tests:

```powershell
python manage.py test ems.tests
```

## GitHub Actions CI

A CI workflow is configured in `.github/workflows/backend-ci.yml`.
It installs dependencies, runs Django system checks, and executes the `ems.tests` suite.

## Useful commands

```powershell
python manage.py check
python manage.py test ems.tests
python manage.py runserver
.\dev.ps1
```

## Notes

- The backend uses JWT authentication via `djangorestframework_simplejwt`.
- Token refresh, verify, logout, and password reset endpoints are available under `/api/auth/`.
- Legacy `accounts` and `reports` app modules were removed; `ems` is now the consolidated API entry point.
- For production, ensure `DEBUG=False`, `SECRET_KEY` is strong, and `FORCE_SSL=True` if behind HTTPS.
- Use `ALLOWED_HOSTS` to specify your production domains, and disable `CORS_ALLOW_ALL_ORIGINS`.
- Set `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, and `CSRF_TRUSTED_ORIGINS` for browser-based authentication.
- The CI workflow validates production config and prevents duplicate auth route include mappings.
