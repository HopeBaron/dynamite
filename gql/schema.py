import strawberry

from gql.input import *
from gql.types import *
import models
from db import Database


@strawberry.type
class Query:
    @strawberry.field
    def tables(self,  limit: int = 100) -> List[Table]:
        return get_entity('tables', Table, limit)

    @strawberry.field
    def reports(self, limit: int = 100) -> List[Report]:
        return get_entity('reports', Report, limit)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_table(self, input: TableInput) -> Table:
        return create_entity('tables', input, Table)

    @strawberry.mutation
    def create_report(self, input: ReportInput) -> Report:
        return create_entity('reports', input, Report)


def transform(cls, entity):
    pydantic = cls._pydantic_type
    return cls.from_pydantic(pydantic(**entity))


def get_entity(collection: str, cls, limit=100):
    db = Database.instance()
    _collection = db[collection]
    entities = _collection.find().limit(limit)
    return [transform(cls, entity) for entity in entities]


def create_entity(collection: str, input: TableInput, cls):
    db = Database.instance()
    _collection = db[collection]
    model_input = input.to_pydantic()
    model_dict = model_input.dict(exclude_unset=True)
    object_id = _collection.insert_one(model_dict).inserted_id
    stored_object = _collection.find_one({'_id': object_id})
    return transform(cls, stored_object)


schema = strawberry.Schema(Query, Mutation, scalar_overrides={
                           models.PyObjectId: ObjectIdScalar})
