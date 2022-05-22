import strawberry

from gql.input import *
from gql.types import *
import models


@strawberry.type
class Query:
    @strawberry.field
    def tables(self,  limit: int = 100) -> List[TableType]:
        return get_entity(TableType, limit)

    @strawberry.field
    def reports(self, limit: int = 100) -> List[ReportType]:
        return get_entity(ReportType, limit)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_table(self, input: TableInput) -> TableType:
        return create_entity(input, TableType)

    @strawberry.mutation
    def create_report(self, input: ReportInput) -> ReportType:
        return create_entity(input, ReportType)


def get_entity(cls, limit=100):
    return cls.find_many(limit=limit)
    

def modelize_input(input):
    model_input = input.to_pydantic()
    return model_input.dict(exclude_unset=True)

async def create_entity(input, cls):
    model = modelize_input(input)
    type = cls(**model)
    obj = type.to_pydantic()
    return await obj.insert()


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
                           models.ColumnReferenceNotation: ColumnReferenceNotationScaler,
                           PydanticObjectId: ObjectIdScalar
                           })
