from typing import Any

from fastapi import Request
from strawberry import BasePermission
from strawberry.types import Info

from auth import Auth


class IsAuthenticated(BasePermission):
    message = "User is not authenticated."

    async def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request: Request = info.context['request']
        token = request.headers['Authorization']
        return await Auth().verify_token(token)
