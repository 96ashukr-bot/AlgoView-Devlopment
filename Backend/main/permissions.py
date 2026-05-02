from typing import Optional

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Role, Permission, RolePermission

from rest_framework.permissions import IsAdminUser,IsAuthenticated

from rest_framework import permissions


SUPERADMIN_ROLE_ALIASES = {"super-admin", "superadmin"}
ADMIN_ROLE_ALIASES = {"admin", "sub-admin", "subadmin"}
USER_ROLE_ALIASES = {"user", "client"}


def get_role_name(user) -> str:
    return (getattr(getattr(user, "role", None), "name", "") or "").strip().lower()


def get_canonical_role(user) -> Optional[str]:
    if not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False):
        return "superadmin"

    role_name = get_role_name(user)
    if role_name in SUPERADMIN_ROLE_ALIASES:
        return "superadmin"
    if role_name in ADMIN_ROLE_ALIASES:
        return "admin"
    if (
        role_name in USER_ROLE_ALIASES
        or getattr(user, "type_of_user", None) == "is_client"
        or getattr(user, "is_client", None) is True
        or str(getattr(user, "is_client", "")).lower() == "true"
    ):
        return "user"
    return None


def is_superadmin_user(user) -> bool:
    return get_canonical_role(user) == "superadmin"


def is_admin_user(user) -> bool:
    return get_canonical_role(user) == "admin"


def is_admin_or_superadmin(user) -> bool:
    return get_canonical_role(user) in {"superadmin", "admin"}


def is_end_user(user) -> bool:
    return get_canonical_role(user) == "user"


def is_platform_admin(user) -> bool:
    return is_admin_or_superadmin(user) or bool(getattr(user, "is_staff", False))


def can_access_client_record(actor, client) -> bool:
    if not actor or not getattr(actor, "is_authenticated", False) or not client:
        return False
    if actor.id == client.id:
        return True
    if is_platform_admin(actor):
        return True
    return getattr(client, "created_by_id", None) == getattr(actor, "id", None)

class IsAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow users with the role 'Admin' to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_admin_or_superadmin(request.user))


class IsSuperadminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_superadmin_user(request.user))


class IsAdminOrSuperadmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_admin_or_superadmin(request.user))


class IsBrokerOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to the broker owner or trusted admin/operator roles.
    """

    def has_object_permission(self, request, view, obj):
        return can_access_client_record(request.user, getattr(obj, "client", None))

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class UpdateRolePermissionsView(APIView):
    permission_classes = [IsAdminOrSuperadmin]
    def post(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

        permissions_data = request.data
        if not isinstance(permissions_data, dict):
            return Response({"error": "Invalid payload format. Expected a dictionary of permissions."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the role_permission or create it if it doesn't exist
        role_permission, _ = RolePermission.objects.get_or_create(role=role)

        for group, permission_actions in permissions_data.items():
            for action, allowed in permission_actions.items():
                # Get the permission if it exists
                permission, _ = Permission.objects.get_or_create(
                    group=group,
                    permission=action
                )

                # If permission should be allowed, link it to the role, otherwise, remove it
                if allowed:
                    role_permission.permissions.add(permission)
                else:
                    role_permission.permissions.remove(permission)

        return Response({"success": "Permissions updated successfully"}, status=status.HTTP_200_OK)
class RolePermissionListView(APIView):
    pagination_class = None
    permission_classes = [IsAdminOrSuperadmin]
    def get(self, request, *args, **kwargs):
        from main.serializers import RolePermissionSerializer

        queryset = RolePermission.objects.all()
        serializer = RolePermissionSerializer(queryset, many=True)  # Use the modified serializer
        return Response(serializer.data, status=status.HTTP_200_OK)
