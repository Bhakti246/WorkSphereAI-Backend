"""Utility helpers for EMS refactor."""

def now_iso():
    from django.utils import timezone
    return timezone.now().isoformat()
