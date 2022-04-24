from bson import ObjectId as BsonObjectId
from bson.errors import InvalidId
from typing import Any, List, Optional
from pydantic import BaseModel as PydanticModel, validator
import pydantic


class PyObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return cls(v)
        except InvalidId:
            raise ValueError(f'{v} is not a valid ObjectId')

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class ObjectIdModel(PydanticModel):
    id: Optional[PyObjectId] = pydantic.Field(alias='_id')

    class Config:
        json_encoders = {
            PyObjectId: str
        }
        allow_population_by_field_name = True


class TableColumn(PydanticModel):
    ref_name: str
    name: str
    foreign_key: str
    type: int


class Table(ObjectIdModel):
    ref_name: str
    name: str
    columns: List[TableColumn] = []


class Condition(PydanticModel):
    operation: str
    target: str
    value: List[str]


class ConditionGroup(PydanticModel):
    operation: str
    conditions: List[Condition]


class ReportColumn(PydanticModel):
    index: int
    ref_name: str
    name: str
    value: str


class Report(ObjectIdModel):
    ref_name: str
    name: str
    columns: List[ReportColumn] = []
    conditions: List[ConditionGroup] = []

