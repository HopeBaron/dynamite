from beanie.odm.operators.find.comparison import In
from strawberry.types import Info

from auth import Auth
from gql.input import *
from gql.permissions import IsAuthenticated, IsOrganizationUser
from gql.types import *
from models import Report, User, Entity
from utils import *


@strawberry.type
class Query:

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user(self, document_id: PydanticObjectId) -> UserType | None:
        return await User.get(document_id)
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def entities(self, info: Info, limit: int = 100) -> list[EntityType]:
        session: models.Session = info.context["session"]
        condition = Entity.owner == session.user and In(Entity.id, session.database_access)
        if session.context:
            return await Entity.find(condition, limit=limit, fetch_links=True).to_list()
        return await Entity.find(limit=limit, fetch_links=True).to_list()
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def reports(self, info: Info, limit: int = 100) -> list[ReportType]:
        session = info.context["session"]
        if session.context:
            return await Report.find(Report.context == session.context,fetch_links=True, limit=limit).to_list()
        return await Report.find(limit=limit, fetch_links=True).to_list()

@strawberry.type
class Mutation:

    @strawberry.mutation(IsOrganizationUser)
    async def request_token(
            self,
            info: Info,
            context: str = None,
            database_access: List[ObjectId] = [],
            conditions: List[ConditionGroupInput] = []) -> str:

        session = info.context["session"]
        entities = link(Entity, database_access)
        slave_session = await session.create_slave_session(context, entities, conditions)
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

    @strawberry.mutation(permission_classes=[IsOrganizationUser])
    async def create_entity(self, input: EntityInput, info: Info) -> EntityType:
        session = info.context["session"]
        entity = input.to_pydantic()
        entity.owner = session.user
        return await entity.save()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report(self, input: ReportInput, info: Info) -> ReportType:
        session = info.context["session"]
        database_access = session.database_access
        permitted_columns = [access.ref.id[0] for access in database_access]
        report = input.to_pydantic()
        report.owner = session
        report.context = session.context
        for column in report.columns:
            entity = await Entity.has_property(column.prop)
            if not len(permitted_columns) == 0 and entity.id not in permitted_columns:
                raise ValueError(f"{entity.id} is not in your access scope.")

        return await report.save()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report_column(self, input: ReportColumnInput) -> ReportColumnType:
        return await create_model(input)

    @strawberry.mutation(permission_classes=[IsOrganizationUser])
    async def create_property(self, input: PropertyInput) -> PropertyType:
        return await create_model(input)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    PydanticObjectId: ObjectId
})
