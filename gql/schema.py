from typing import List

import models
from auth import Auth
from gql.input import *
from gql.permissions import IsAuthenticated
from gql.types import *
from models import Report, User, Entity, Property
from utils import *


@strawberry.type
class Query:

    @strawberry.field(permission_classes=[IsAuthenticated])
    def user(self, document_id: PydanticObjectId) -> UserType:
        return get_model(User, document_id=document_id)

    @strawberry.field
    async def verify_token(self, token: str) -> bool:
        return await Auth().verify_token(token)

    @strawberry.field
    async def entities(self, limit: int = 100) -> List[EntityType]:
        return await get_models(Entity, limit)

    @strawberry.field
    async def reports(self, limit: int = 100) -> List[ReportType]:
        return await get_models(Report, limit)

    @strawberry.field
    async def properties(self, limit: int = 100) -> List[PropertyType]:
        return await get_models(Property, limit)


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def create_user(self, input: UserInput) -> UserType:
        return UserType.from_pydantic(await User.create_user(input))

    @strawberry.mutation
    async def authenticate_user(self, username: str, password: str) -> LoginResult:
        user = await User.validate_credentials(username, password)
        if not user:
            return LoginError("Username or password are invalid.")
        session = await Auth().form_token(user)
        return LoginSuccess(user, session.token)

    @strawberry.mutation
    async def create_entity(self, input: EntityInput) -> EntityType:
        return await create_model(input)
    @strawberry.mutation
    async def create_report(self, input: ReportInput) -> ReportType:
        return await create_model(input)

    @strawberry.mutation
    async def create_report_column(self, input: ReportColumnInput) -> ReportColumnType:
        return await create_model(input)

    @strawberry.mutation
    async def create_property(self, input: PropertyInput) -> PropertyType:
        return await create_model(input)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    PydanticObjectId: ObjectId
})
