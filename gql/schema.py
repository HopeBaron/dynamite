from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
import strawberry
from gql.input import *
from gql.types import *
from utils import *
from models import Report, Table, User


@strawberry.type
class Query:
    @strawberry.field
    def users(self, limit: int = 100) -> List[UserType]:
        return get_entities(User, limit)

    def user(self, id: PydanticObjectId) -> UserType:
        return get_entity(User, id)

    @strawberry.field
    def tables(self,  limit: int = 100) -> List[TableType]:
        return get_entities(Table, limit)

    @strawberry.field
    def table(self, id: PydanticObjectId) -> TableType:
        return get_entity(Table, id)

    @strawberry.field
    def reports(self, limit: int = 100) -> List[ReportType]:
        return get_entities(Report, limit)

    @strawberry.field
    def report(self, id: PydanticObjectId) -> ReportType:
        return get_entity(Report, id)


@strawberry.type
class Mutation:
    
    @strawberry.mutation
    def create_user(self, input: UserInput) -> UserType:
        return create_entity(User, input)

    @strawberry.mutation
    def create_table(self, input: TableInput) -> TableType:
        return create_entity(Table, input)

    @strawberry.mutation
    def create_report(self, input: ReportInput) -> ReportType:
        return create_entity(Report, input)

    @strawberry.mutation
    def delete_table(self, id: PydanticObjectId) -> TableType | None:
        return delete_entity(Table, id)

    @strawberry.mutation
    def delete_report(self, id: PydanticObjectId) -> ReportType | None:
        return delete_entity(Report, id)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
                           models.ColumnReferenceNotation: ColumnReferenceNotationScaler,
                           PydanticObjectId: ObjectIdScalar
                           })
