import itertools
from datetime import datetime
from functools import reduce, partial
from typing import List, Optional, Iterable, Any

import bcrypt
import pymongo
from beanie import Document, Link, PydanticObjectId, Indexed
from pydantic import BaseModel, validator, Field
from pymongo import IndexModel
from six import string_types
from sql import Column, Table, Join
from typing_extensions import Self

from enums import PropertyTypes, ColumnJoins, WhereOperations, ConditionGroupOperations
from utils import create_model, get_model, normalize, sort_by_index, reduce_conditions, operators_dict, joins_dict, \
    group_operators_dict


class EmbeddedDocument(BaseModel):
    id: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")


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
        return await create_model(input)

    @staticmethod
    async def validate_credentials(username: str, password: str):
        user: User = await get_model(User, username=username)
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


class Property(DatabaseModel, Document):
    type: PropertyTypes = PropertyTypes.STRING
    entity: Link["Entity"]
    refers_to: Optional[Link["Property"]]

    async def sql(self):
        entity = await self.entity.fetch()
        table = entity.sql()
        column_name = self.database_name
        return table.__getattr__(column_name)

    class Settings:
        indexes = [
            IndexModel([("entity", pymongo.ASCENDING), ("database_name", pymongo.ASCENDING)], unique=True,
                       name="entity_name_index")
        ]

    @property
    def references(self):
        return Property.find(Property.refers_to.id == self.id)


class Entity(DatabaseModel, Document):
    pivot: bool = False

    def prop(self, item):
        pass

    @property
    def properties(self):
        return Property.find(Property.entity.id == self.id)

    def sql(self):
        return Table(self.database_name)

    class Settings:
        indexes = [
            IndexModel([("database_name", pymongo.ASCENDING)], unique=True, name="database_name_index")
        ]


Entity.update_forward_refs()

Property.update_forward_refs()


class TableJoin(EmbeddedDocument):
    type: ColumnJoins = ColumnJoins.INNER
    columns: List[Link[Property]]

    def sql(self):
        picked_join = joins_dict[self.type]
        columns = [column.sql() for column in self.columns]
        tables = [column.table for column in columns]
        current_join = reduce(lambda a, b: picked_join(a, b), tables)
        (condition, _) = reduce(reduce_conditions, columns)
        current_join.condition = condition
        return current_join


class Condition(EmbeddedDocument):
    operation: WhereOperations
    index: int = 0
    target: PydanticObjectId
    value: List[str]

    async def sql(self):
        mapped_function = operators_dict[self.operation]
        target = await self.as_property()
        column = await target.sql()
        return mapped_function(column, self.value)

    async def as_property(self):
        return await Property.get(self.target)


class ConditionGroup(EmbeddedDocument):
    operation: ConditionGroupOperations
    index: int = 0
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)

    async def as_properties(self):
        return [await condition.as_property() for condition in self.conditions]

    async def sql(self):
        operation = self.operation
        wheres = [await condition.sql() for condition in self.conditions]
        partial_reduce = partial(reduce_conditions, operator=operation)
        return reduce(partial_reduce, wheres)


class ReportColumn(DatabaseModel, Document):
    index: int = 0
    report: Link["Report"]
    property: Link[Property]

    def sql(self):
        return self.property.sql()
class Query(BaseModel):
    select: str
    values: List[str]
class Report(DatabaseModel, Document):
    condition_groups: List[ConditionGroup] = []
    joins: List[TableJoin] = []
    _sort_condition_groups = validator(
        'condition_groups', allow_reuse=True)(sort_by_index)

    def columns(self, fetch_links: bool = True):
        return ReportColumn.find(ReportColumn.report.id == self.id, fetch_links=fetch_links)

    async def sql(self):
        all_tables = {}

        async def append(prop):
            entity = await prop.entity.fetch()
            table = entity.sql()
            all_tables[entity.database_name] = table

        columns = await self.columns().to_list()
        properties = [column.property for column in columns]
        condition_groups = self.condition_groups
        condition_props = [await cond.as_properties() for cond in condition_groups]
        condition_chained = [item for sublist in condition_props for item in sublist]
        for p in properties:
            await append(p)
        for c in condition_chained:
            await append(c)
        tables: Join = reduce(lambda a, b: a.join(b), all_tables.values())

        async def get_col(prop: Property):
            entity = await prop.entity.fetch()
            table = all_tables[entity.database_name]
            return table.__getattr__(prop.database_name)

        column_names = [await get_col(prop) for prop in properties]
        select = tables.select(*column_names)
        groups = []
        for condition_group in condition_groups:
            operation = condition_group.operation
            wheres = []
            mapped_function = group_operators_dict[operation]
            for condition in condition_group.conditions:
                operator_function = operators_dict[condition.operation]
                prop = await condition.as_property()
                entity = await  prop.entity.fetch()
                table = all_tables[entity.database_name]
                col = table.__getattr__(prop.database_name)
                cond = operator_function(col, condition.value)
                wheres.append(cond)
            coupled = reduce(lambda a, b: mapped_function(a, b), wheres)
            groups.append(coupled)
        select.where = reduce(lambda a, b: group_operators_dict[ConditionGroupOperations.AND](a, b), groups)
        s = tuple(select)
        return Query(select=s[0], values=s[1])

ReportColumn.update_forward_refs()
