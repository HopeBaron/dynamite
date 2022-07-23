from datetime import datetime
from functools import reduce, partial
from typing import List, Optional

import bcrypt
import pymongo
from beanie import Document, Link, PydanticObjectId, Indexed
from pydantic import BaseModel, validator, Field
from pymongo import IndexModel
from sql import Column, Table
from typing_extensions import Self

from enums import PropertyTypes, ColumnJoins, WhereOperations, ConditionGroupOperations
from utils import create_model, get_model, normalize, sort_by_index, reduce_conditions, operators_dict, joins_dict


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
        await self.fetch_all_links()
        table = self.entity.sql()
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
    target: Link[Property]
    value: List[str]

    def sql(self):
        mapped_function = operators_dict[self.operation]
        target = self.target
        column = target.sql()
        return mapped_function(column, self.value)


class ConditionGroup(EmbeddedDocument):
    operation: ConditionGroupOperations
    index: int = 0
    conditions: List[Condition]

    _sort_conditions = validator('conditions', allow_reuse=True)(sort_by_index)

    def sql(self):
        operation = self.operation
        wheres = [condition.sql() for condition in self.conditions]
        partial_reduce = partial(reduce_conditions, operator=operation)
        return reduce(partial_reduce, wheres)


class ReportColumn(DatabaseModel, Document):
    index: int = 0
    report: Link["Report"]
    property: Link[Property]

    def sql(self):
        return self.property.sql()


class Report(DatabaseModel, Document):
    condition_groups: List[ConditionGroup] = []
    joins: List[TableJoin] = []
    _sort_condition_groups = validator(
        'condition_groups', allow_reuse=True)(sort_by_index)

    def columns(self, fetch_links: bool = True):
        return ReportColumn.find(ReportColumn.report.id == self.id, fetch_links=fetch_links)

    def __construct_condition_groups(self):
        groups_sql = [condition_group.sql() for condition_group in self.condition_groups]
        if not groups_sql:
            return None
        return reduce(reduce_conditions, groups_sql)

    def __construct_joins(self):
        joins = [join.sql() for join in self.joins]
        if not joins:
            return None
        return reduce(lambda first, second: first.join(second), joins)

    async def __construct_columns(self):
        cols = [await column.sql() async for column in self.columns()]
        if not cols:
            return None
        tables = [col.table for col in cols]
        joined_tables = reduce(lambda first, second: first.join(second), tables)
        print("Dingo", cols, joined_tables, type(joined_tables))
        return joined_tables.select(*cols)

    async def sql(self):
        columns = await self.__construct_columns()
        if not columns:
            return None
        joins = self.__construct_joins()
        final = columns.join(joins) if joins else columns
        groups = self.__construct_condition_groups()
        if groups:
            final.condition = groups
        return str(final)


ReportColumn.update_forward_refs()
