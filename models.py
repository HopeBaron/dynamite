import asyncio
import concurrent
from datetime import datetime
from functools import reduce, partial
from typing import List, Optional

import bcrypt
from beanie import Document, Link, PydanticObjectId
from pydantic import BaseModel, validator, Field, root_validator
from sql import Column
from typing_extensions import Self

from enums import PropertyTypes, ColumnJoins, WhereOperations, ConditionGroupOperations
from utils import create_entity, get_entity, normalize, sort_by_index, reduce_conditions, operators_dict, joins_dict


class EmbeddedDocument(BaseModel):
    id: Optional[PydanticObjectId] = Field(default=PydanticObjectId(), alias="_id")


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


class Property(DatabaseModel):
    type: PropertyTypes = PropertyTypes.STRING
    reference: Optional["PropertyReference"]


class Entity(DatabaseModel, Document):
    pivot: bool = False
    properties: List[Property] = []

    @validator("properties", pre=True)
    def prioritize_references(cls, value):
        value.sort(key=lambda prop: 0 if prop.reference else 1)
        return value

    def __getattr__(self, item):
        filtered_props = filter(lambda prop: prop.database_name == item, self.properties)
        return next(filtered_props, None)


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

    def sql(self) -> Column:
        return Column(self.entity, self.property)


def property_reference(value: str):
    stripped_dot_notation = value.strip().split('.')
    if len(stripped_dot_notation) != 2:
        message = f"column reference must be in the form of 'table.column' but was {value}"
        raise Exception(message)
    normalized_values = [normalize(v) for v in stripped_dot_notation]
    entity, prop = normalized_values
    return PropertyReference(entity=entity, property=prop)


Property.update_forward_refs()


class Tree(Document):
    children: List[Entity]

    @validator('children', pre=True)
    def prioritize_pivots(cls, value):
        def sort(element: Entity):
            return 0 if element.pivot else 1

        value.sort(key=sort)
        return value


class TableJoin(BaseModel):
    type: ColumnJoins = ColumnJoins.INNER
    columns: List[PropertyReference]

    def sql(self):
        picked_join = joins_dict[self.type]
        columns = [column.sql() for column in self.columns]
        tables = [column.table for column in columns]
        current_join = reduce(lambda a, b: picked_join(a, b), tables)
        (condition, _) = reduce(reduce_conditions, columns)
        current_join.condition = condition
        return current_join


class Condition(BaseModel):
    operation: WhereOperations
    index: int = 0
    target: PropertyReference
    value: List[str]

    def sql(self):
        mapped_function = operators_dict[self.operation]
        target = self.target
        column = target.sql()
        return mapped_function(column, self.value)


class ConditionGroup(BaseModel):
    operation: ConditionGroupOperations
    index: int = 0
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)

    def sql(self):
        operation = self.operation
        wheres = [condition.sql() for condition in self.conditions]
        partial_reduce = partial(reduce_conditions, operator=operation)
        return reduce(partial_reduce, wheres)


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

    def __construct_condition_groups(self):
        groups_sql = [condition_group.sql() for condition_group in self.condition_groups]
        return reduce(reduce_conditions, groups_sql)

    def __construct_joins(self):
        joins = [join.sql() for join in self.joins]
        initial = joins.pop()
        return reduce(lambda first, second: first.join(second), joins, initial.sql())

    def __construct_columns(self):
        return [column.sql() for column in self.columns]

    def sql(self):
        joins = self.__construct_joins()
        groups = self.__construct_condition_groups()
        columns = self.__construct_columns()
        joins.select(columns)
        joins.condition = groups
        return str(joins)
