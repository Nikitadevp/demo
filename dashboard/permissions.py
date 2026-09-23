"""
permissions.py — replaces the earlier session-reading version now that
SessionAdminAuthentication (authentication.py) populates request.user with
the actual AdminUser instance. Standard DRF style from here on.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _get_project(obj):
    if hasattr(obj, "project"):
        return obj.project
    if hasattr(obj, "site"):
        return obj.site.project
    if hasattr(obj, "instance"):
        return obj.instance.site.project
    if hasattr(obj, "checklist_item_result"):
        return obj.checklist_item_result.instance.site.project
    return None


class IsQCLoggedIn(BasePermission):
    """Any of the 4 QC roles — replaces DRF's IsAuthenticated, since
    request.user here is our AdminUser bridge, not Django's auth user."""

    message = "Please log in."

    def has_permission(self, request, view):
        role = getattr(request.user, "role", None)
        return role in ("L1 Inspector", "L2 Verifier", "L3 PM", "Viewer")


class IsProjectMember(BasePermission):
    """
    v1: no project-level scoping yet (10-15 users, single company) — every
    logged-in QC role can see every project. Add a `projects` ManyToMany on
    AdminUser and filter here once scoping is actually needed.
    """

    def has_object_permission(self, request, view, obj):
        return True  # tighten later: request.user.projects.filter(...)


class CanFillChecklist(BasePermission):
    """L1 Inspector only — create/edit checklist instances and item results."""

    message = "Only L1 Inspectors can fill or edit checklists."

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "L1 Inspector"

    def has_object_permission(self, request, view, obj):
        instance = obj if hasattr(obj, "filled_by") else obj.instance
        return instance.filled_by_id == request.user.id


class CanVerifyChecklist(BasePermission):
    """L2 Verifier only — approve/reject items filled by L1."""

    message = "Only L2 Verifiers can verify checklist items."

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "L2 Verifier"


class CanRaiseIssue(BasePermission):
    """L2 Verifier or L3 PM — L1 is explicitly blocked."""

    message = "Only L2 Verifiers or L3 PMs can raise issues."

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) in ("L2 Verifier", "L3 PM")


class CanAudit(BasePermission):
    """L3 PM only — random independent audits."""

    message = "Only L3 PMs can perform audits."

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "L3 PM"


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS