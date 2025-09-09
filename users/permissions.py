from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


def is_accessible(*roles: str) -> type[BasePermission]:
    class _IsAccessible(BasePermission):
        def has_permission(self, request: Request, view: APIView) -> bool:
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if len(roles) == 0:
                return True
            if user.role not in roles:
                raise PermissionDenied(
                    detail={
                        "message": f"user requires any of the following: ({', '.join(roles)}) roles to proceed"
                    }
                )
            return True

    return _IsAccessible
