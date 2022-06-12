from typing import Any

from strawberry import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    message = "User is not authenticated."

    async def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        return info.context["user"] is not None
