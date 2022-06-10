from auth import Auth
from auth import Auth
from gql.input import *
from gql.permissions import IsAuthenticated
from gql.types import *
from models import Report, Table, User
from utils import *


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def users(self, limit: int = 100) -> List[UserType]:
        return get_entities(User, limit)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def user(self, document_id: PydanticObjectId) -> UserType:
        return get_entity(User, document_id=document_id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def tables(self, limit: int = 100) -> List[TableType]:
        return get_entities(Table, limit)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def table(self, document_id: PydanticObjectId) -> TableType:
        return get_entity(Table, document_id=document_id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def reports(self, limit: int = 100) -> List[ReportType]:
        return get_entities(Report, limit)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def report(self, document_id: PydanticObjectId) -> ReportType:
        return get_entity(Report, document_id=document_id)

    @strawberry.field
    async def verify_token(self, token: str) -> bool:
        return await Auth().verify_token(token)


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def create_user(self, input: UserInput) -> UserType:
        return UserType.from_pydantic(await User.create_user(input))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_table(self, input: TableInput) -> TableType:
        return await create_entity(Table, input)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_report(self, input: ReportInput) -> ReportType:
        return await create_entity(Report, input)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_table(self, id: PydanticObjectId) -> TableType | None:
        return await delete_entity(Table, id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_report(self, id: PydanticObjectId) -> ReportType | None:
        return await delete_entity(Report, id)

    @strawberry.mutation
    async def authenticate_user(self, username: str, password: str) -> LoginResult:
        user = await User.validate_credintials(username, password)
        if not user:
            return LoginError("Username or password are invalid.")
        session = await Auth().form_token(user)
        return LoginSuccess(user, session.token)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
    models.ColumnReferenceNotation: ColumnReferenceNotationScaler,
    PydanticObjectId: ObjectIdScalar
})
