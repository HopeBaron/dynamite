from typing import List

from sql.operators import In
from strawberry.types import Info

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
    async def entities(self, info: Info, limit: int = 100) -> List[EntityType]:
        current_session: models.Session = info.context["session"]
        condition = Entity.owner == current_session.user and In(Entity.id, current_session.database_access)
        return await Entity.find(condition, fetch_links=True).to_list()

    @strawberry.field
    async def reports(self, limit: int = 100) -> List[ReportType]:
        return await get_models(Report, limit)

    @strawberry.field
    async def properties(self, limit: int = 100) -> List[PropertyType]:
        return await get_models(Property, limit)


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def request_token(
            self,
            info: Info,
            database_access: List[ObjectId] = [],
            conditions: List[ConditionGroupInput] = []) -> str:

        session = info.context["session"]
        entities = link(Entity, database_access)
        slave_session = await session.create_slave_session(entities, conditions)
        await slave_session.save()
        return slave_session.token


    @strawberry.mutation
    async def create_user(self, input: UserInput) -> UserType:
        user = await User.create_user(input.username, input.password)
        return UserType.from_pydantic(user)

    @strawberry.mutation
    async def authenticate_user(self, username: str, password: str) -> LoginResult:
        user = await User.validate_credentials(username, password)
        if not user:
            return LoginError("Username or password are invalid.")
        session = Auth().create_session(user)
        await session.save()
        return LoginSuccess(user, session.token)

    @strawberry.mutation
    async def create_entity(self, input: EntityInput, info: Info) -> EntityType:
        session = info.context["session"]
        entity = input.to_pydantic()
        entity.owner = session.user
        await entity.save()
        await create_models(input.properties, entity=entity.id)
        return entity

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report(self, input: ReportInput, info: Info) -> ReportType:
        session = info.context["session"]
        permitted_columns = session.database_access
        columns = [column.to_pydantic() for column in input.columns]
        report = input.to_pydantic()
        report.owner = session
        for column in columns:
            await column.fetch_all_links()
            column.report = link(Report, report.id)
            property = column.property
            entity = await property.entity.fetch()


            if not len(permitted_columns) == 0 and entity.id not in permitted_columns:
                raise ValueError(f"{entity.id} is not in your access scope.")

        return await report.save()
        await ReportColumn.insert_many(columns)

    @strawberry.mutation
    async def create_report_column(self, input: ReportColumnInput) -> ReportColumnType:
        return await create_model(input)

    @strawberry.mutation
    async def create_property(self, input: PropertyInput) -> PropertyType:
        return await create_model(input)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    PydanticObjectId: ObjectId
})
