"""
authentication.py — add this file inside your demo app.

Bridges your existing session-based AdminUser login into DRF's request.user.
Does NOT touch login_view or the AdminUser model — read-only bridge.

Register it in settings.py:

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "demo.authentication.SessionAdminAuthentication",
        ],
    }
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import AdminUser


class SessionAdminAuthentication(BaseAuthentication):
    def authenticate(self, request):
        admin_id = request.session.get("admin_id")
        if not admin_id:
            return None  # let DRF fall through to unauthenticated (AnonymousUser)

        try:
            admin = AdminUser.objects.get(id=admin_id, is_active=True)
        except AdminUser.DoesNotExist:
            raise AuthenticationFailed("Session invalid or user inactive")

        return (admin, None)  # becomes request.user, request.auth