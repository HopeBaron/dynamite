import strawberry

from gql.input import *
from gql.types import *
from models import Report, Table


@strawberry.type
class Query:
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


async def get_entities(cls, limit=100):
    return await cls.find_many(limit=limit)


async def get_entity(cls:Table , id: PydanticObjectId):
    return await cls.find_one(cls.id == id)


def modelize_input(input):
    model_input = input.to_pydantic()
    return model_input.dict(exclude_unset=True)


def get_object(cls, input):
    model = modelize_input(input)
    return cls(**model)


async def create_entity(cls, input):
    obj = get_object(cls, input)
    return await obj.insert()


async def delete_entity(cls, id):
    entity = await get_entity(cls, id)
    if entity is None:
        return None
    await entity.delete()
    return entity


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
                           models.ColumnReferenceNotation: ColumnReferenceNotationScaler,
                           PydanticObjectId: ObjectIdScalar
                           })
