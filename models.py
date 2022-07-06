import sys
from datetime import datetime
from enum import Enum
from functools import reduce
from typing import List, Optional

import bcrypt
import strawberry
from beanie import Document, Link
from pydantic import BaseModel, validator
from typing_extensions import Self

from utils import create_entity, get_entity, normalize, sort_by_index


class DatabaseModel(BaseModel):
    database_name: str
    display_name: str

    _normalize_database_name = validator('database_name', allow_reuse=True)(normalize)


class User(Document):
    username: str
    password: str

    @classmethod
    async def create_user(cls, input) -> Self:
        username = input.username
        matching_users = await User.find(username=username).count()
        if matching_users != 0:
            raise ValueError("This username is already taken.")
        encoded_password = input.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(encoded_password, salt)
        input.password = hashed
        return await create_entity(User, input)

    @staticmethod
    async def validate_credintials(username: str, password: str):
        user: User = await get_entity(User, username=username)
        if not user:
            return None
        hashed_password = user.password.encode('utf-8')
        encoded_password = password.encode('utf-8')
        correct_password = bcrypt.checkpw(encoded_password, hashed_password)
        if correct_password:
            return user

        return None


class Session(Document):
    token: str
    user: Link[User]
    used_since: datetime
    exp: datetime


@strawberry.enum
class PropertyType(Enum):
    NUMBER = "Number"
    STRING = "String"
    BOOLEAN = "Boolean"


@strawberry.enum
class ConditionGroupOperation(Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


@strawberry.enum
class WhereOperation(Enum):
    EQ = "EQ"
    IN = "IN"

    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "lTE"
    NEQ = "NEQ"


@strawberry.enum
class ColumnJoin(Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"


class Property(DatabaseModel):
    type: PropertyType = PropertyType.STRING
    reference: "PropertyReference" | None = None


class EntityType(Enum):
    MODEL = "Model"
    PIVOT = "Pivot"


class Entity(DatabaseModel, Document):
    type: EntityType = EntityType.MODEL
    properties: List[Property] = []

    @validator("properties")
    def prioritize_references(self, value):
        value.sort(key=lambda prop: prop.reference)

    def __getattr__(self, item):
        return next(filter(lambda prop: prop.database_name == item, self.properties), None)


def stringify_property_reference(dot_notation) -> str:
    return str(property_reference(dot_notation))


class PropertyReference(BaseModel):
    entity: str
    property: str

    def __str__(self) -> str:
        return f'{self.entity}.{self.property}'

    async def get_entity(self) -> Entity:
        name = self.entity
        entity = await Entity.find_one(Entity.database_name == name)
        if not entity:
            no_table_message = f"Entity {name} doesn't exist. Please make sure you registered it."
            raise ValueError(no_table_message)
        return entity

    async def get_property(self) -> Property:
        prop = await self.get_entity().__getattribute__(self.property)
        if not prop:
            no_property_message = f"property {self} doesn't exist."
            raise ValueError(no_property_message)
        return prop


def property_reference(cls, value: str):
    stripped_dot_notation = value.strip().split('.')
    if len(stripped_dot_notation) != 2:
        message = f"column reference must be in the form of 'table.column' but was {value}"
        raise Exception(message)
    normalized_values = [normalize(v) for v in stripped_dot_notation]
    entity, prop = normalized_values
    return cls(entity=entity, property=prop)


class TableJoin(BaseModel):
    type: ColumnJoin = ColumnJoin.INNER
    columns: List[PropertyReference]


class Condition(BaseModel):
    operation: WhereOperation
    index: int = sys.maxsize
    target: PropertyReference
    value: List[str]


class ConditionGroup(BaseModel):
    operation: ConditionGroupOperation
    index: int = sys.maxsize
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)


class ReportColumn(DatabaseModel):
    index: int = 0
    value: PropertyReference


class Report(DatabaseModel, Document):
    columns: List[ReportColumn] = []
    condition_groups: List[ConditionGroup] = []
    joins: List[TableJoin] = []
    _sort_condition_groups = validator(
        'condition_groups', allow_reuse=True)(sort_by_index)
    _sort_columns = validator('columns', allow_reuse=True)(sort_by_index)
