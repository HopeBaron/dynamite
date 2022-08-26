import strawberry
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import In
from strawberry.types import Info

from dynamite.auth import Auth
from dynamite.errors import DynamiteError
from dynamite.gql.input import TopicInput, UserInput, ConditionGroupInput, ReportInput
from dynamite.gql.permissions import IsAuthenticated, IsOrganizationUser
from dynamite.gql.types import UserType, LoginSuccess, TopicType, ObjectId, ReportType, DynamiteResult
from dynamite.models import Report, User, Topic, Session
from dynamite.utils import *


@strawberry.type
class Query:

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user(self, document_id: PydanticObjectId) -> UserType | None:
        return await User.get(document_id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def topics(self, info: Info, limit: int = 100) -> list[TopicType]:
        session: Session = info.context["session"]
        condition = Topic.owner == session.user and In(Topic.id, session.topic_access)
        if session.context:
            return await Topic.find(condition, limit=limit, fetch_links=True).to_list()
        return await Topic.find(limit=limit, fetch_links=True).to_list()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def reports(self, info: Info, limit: int = 100) -> list[ReportType]:
        session = info.context["session"]
        if session.context:
            return await Report.find(Report.context == session.context, fetch_links=True, limit=limit).to_list()
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
        entities = link(Topic, database_access)
        slave_session = await session.create_slave_session(context, entities, conditions)
        await slave_session.save()
        return slave_session.token

    @strawberry.mutation
    async def create_user(self, input: UserInput) -> DynamiteResult[UserType]:
        user = await User.create_user(input.username, input.password)
        return UserType.from_pydantic(user)

    @strawberry.mutation
    async def authenticate_user(self, username: str, password: str) -> DynamiteResult[LoginSuccess]:
        user = await User.validate_credentials(username, password)
        if not user:
            return DynamiteError(message="test", code=123)
        session = Auth().create_session(user)
        await session.save()
        return LoginSuccess(user, session.token)

    @strawberry.mutation(permission_classes=[IsOrganizationUser])
    async def create_topic(self, input: TopicInput, info: Info) -> DynamiteResult[TopicType]:
        session = info.context["session"]
        entity = input.to_pydantic()
        entity.owner = session.user
        return await entity.save()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report(self, input: ReportInput, info: Info) -> DynamiteResult[ReportType]:
        session = info.context["session"]
        database_access = session.topic_access
        permitted_columns = [access.ref.id[0] for access in database_access]
        report = input.to_pydantic()
        report.owner = session
        report.context = session.context
        for column in report.columns:
            entity = await Topic.has_detail(column.detail)
            if not len(permitted_columns) == 0 and entity.id not in permitted_columns:
                raise ValueError(f"{entity.id} is not in your access scope.")

        return await report.save()



schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    PydanticObjectId: ObjectId
})
