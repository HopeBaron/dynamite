import strawberry
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import In
from strawberry.types import Info

from dynamite import enums
from dynamite.auth import Auth
from dynamite.gql.input import TopicInput, UserInput, ConditionGroupInput, ReportInput
from dynamite.gql.permissions import IsAuthenticated, IsOrganizationUser
from dynamite.gql.types import UserType, LoginSuccess, TopicType, ObjectId, ReportType, DynamiteResult, \
    DynamiteErrorType, PermittedOperation
from dynamite.models import Report, User, Topic, Session
from dynamite.utils import *


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def operations(self) -> List[PermittedOperation]:
        return [PermittedOperation(type=key, operations=value) for key, value in enums.operations.items()]

    @strawberry.field(permission_classes=[IsAuthenticated])
    def operation(self, type: enums.DetailExpectedType) -> PermittedOperation:
        return PermittedOperation(type=type, operations=enums.operations[type])

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

    @strawberry.mutation(permission_classes=[IsOrganizationUser])
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
        try:
            user: User = await User.create_user(input.username, input.password)
            return UserType.from_pydantic(user)
        except DynamiteError as error:
            return DynamiteErrorType(code=error.code, message=error.message)

    @strawberry.mutation
    async def authenticate_user(self, username: str, password: str) -> DynamiteResult[LoginSuccess]:
        user: User = await User.validate_credentials(username, password)
        if not user:
            return DynamiteErrorType(code=DynamiteErrorTypes.INVALID_LOGIN, message="Username or password are "
                                                                                    "incorrect.")
        session: Session = Auth().create_session(user)
        await session.save()
        return LoginSuccess(user=user, token=session.token)

    @strawberry.mutation(permission_classes=[IsOrganizationUser])
    async def create_topic(self, input: TopicInput, info: Info) -> DynamiteResult[TopicType]:
        try:
            session: Session = info.context["session"]
            topic: Topic = input.to_pydantic()
            topic.owner = session.user
            return await topic.save()
        except DynamiteError as error:
            return DynamiteErrorType(code=error.code, message=error.message)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report(self, input: ReportInput, info: Info) -> DynamiteResult[ReportType]:
        try:
            session = info.context["session"]
            database_access = session.topic_access
            permitted_columns = [access.ref.id[0] for access in database_access]
            report: Report = input.to_pydantic()
            report.owner = session
            report.context = session.context
            for column in report.columns:
                topic: Topic = await Topic.has_detail(column.detail)
                if not len(permitted_columns) == 0 and topic.id not in permitted_columns:
                    raise DynamiteError(DynamiteErrorTypes.NOT_IN_SCOPE, f"{topic.id} is not in your access scope.")

            return await report.save()
        except DynamiteError as error:
            return DynamiteErrorType(code=error.code, message=error.message)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    PydanticObjectId: ObjectId
})
