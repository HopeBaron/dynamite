from datetime import datetime
import sys
from enum import Enum
from typing import List
from typing_extensions import Self
import bcrypt

import strawberry
from beanie import Document, Link
from pydantic import BaseModel, validator

from utils import create_entity, get_entity, normalize, sort_by_index


class User(Document):
    username: str
    name: str
    password: str
    
    @classmethod
    async def create_user(cls, input) -> Self:
        username = input.username
        matching_users = User.find(username=username).count()
        if matching_users != 0:
            raise ValueError("This username is already taken.")
        encoded_password = input.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(encoded_password, salt)
        input.password = hashed
        return create_entity(User, input)

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
class ColumnType(Enum):
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
    EQ = "IN"
    BETWEEN = "BETWEEN"
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="


@strawberry.enum
class ColumnJoin(Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"


class PydanticModel(BaseModel):
    _normalize_ref_name = validator(
        'ref_name', allow_reuse=True, check_fields=False)(normalize)

    def __str__(self) -> str:
        return f'{self.table}.{self.column}'


class TableColumn(PydanticModel):
    ref_name: str
    name: str
    type: ColumnType = ColumnType.STRING


class Table(PydanticModel, Document):
    ref_name: str
    name: str
    columns: List[TableColumn] = []


def column_ref(dot_notation) -> str:
    return str(ColumnReferenceNotation.ref(dot_notation))


class ColumnReferenceNotation(PydanticModel):
    table: str
    column: str

    @classmethod
    def ref(cls, value: str):
        stripped_dot_notation = value.strip().split('.')
        if len(stripped_dot_notation) != 2:
            message = f"column reference must be in the form of 'table.column' but was {value}"
            raise Exception(message)
        normalized_values = [normalize(v) for v in stripped_dot_notation]
        table, column = normalized_values
        return cls(table=table, column=column)

    async def get_table(self) -> Table:
        name = self.table
        table = await Table.find_one(Table.ref_name == name)
        if not table:
            no_table_message = f"table {name} doesn't exist. Please make sure you registered it."
            raise ValueError(no_table_message)
        return table

    async def get_column(self) -> TableColumn:
        table = await self.get_table()
        column = next(filter(lambda column: column.ref_name ==
                      self.column, table.columns), None)
        if not column:
            no_column_message = f"column {self} doesn't exist."
            raise ValueError(no_column_message)
        return column


class Join(PydanticModel):
    type: ColumnJoin = ColumnJoin.INNER
    columns: List[List[ColumnReferenceNotation]]


class Condition(PydanticModel):
    operation: WhereOperation
    index: int = sys.maxsize
    target: ColumnReferenceNotation
    value: List[str]


class ConditionGroup(PydanticModel):
    operation: ConditionGroupOperation
    index: int = sys.maxsize
    conditions: List[Condition]

    _sort_condtions = validator('conditions', allow_reuse=True)(sort_by_index)


class ReportColumn(PydanticModel):
    index: int = sys.maxsize
    ref_name: str
    name: str
    value: ColumnReferenceNotation


class Report(PydanticModel, Document):
    ref_name: str
    name: str
    columns: List[ReportColumn] = []
    condition_groups: List[ConditionGroup] = []
    joins: List[Join] = []
    _sort_condition_groups = validator(
        'condition_groups', allow_reuse=True)(sort_by_index)
    _sort_columns = validator('columns', allow_reuse=True)(sort_by_index)
