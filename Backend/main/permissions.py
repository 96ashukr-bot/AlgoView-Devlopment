from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Role, Permission, RolePermission

class UpdateRolePermissionsView(APIView):
    def post(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

        permissions_data = request.data
        if not isinstance(permissions_data, dict):
            return Response({"error": "Invalid payload format. Expected a dictionary of permissions."}, status=status.HTTP_400_BAD_REQUEST)

        for group, permission_actions in permissions_data.items():
            for action, allowed in permission_actions.items():
                # Find or create the permission for the group and action
                permission, created = Permission.objects.get_or_create(
                    group=group,
                    permission=action
                )

                # If permission should be allowed, link it to the role, otherwise, remove it
                role_permission, _ = RolePermission.objects.get_or_create(role=role)
                if allowed:
                    role_permission.permissions.add(permission)
                else:
                    role_permission.permissions.remove(permission)

        return Response({"success": "Permissions updated successfully"}, status=status.HTTP_200_OK)
