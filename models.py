import asyncio
from enum import Enum
from pprint import pprint
import re
import sys
from tokenize import String
from beanie import Document
from typing import Any, List, Optional, TypeVar
from pydantic import BaseModel, root_validator, validator
import strawberry
from asgiref.sync import async_to_sync


@strawberry.enum
class ColumnType(Enum):
    NUMBER = "Number"
    STRING = "String"


@strawberry.enum
class ConditionGroupOperation(Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


@strawberry.enum
class ConditionOperation(Enum):
    EQ = ("IN", None)
    BETWEEN = ("BETWEEN", 2)
    GT = (">", 1)
    GTE = (">=", 1)
    LT = ("<", 1)
    LTE = ("<=", 1)


@strawberry.enum
class ColumnJoin(Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"


def normalize(value: str) -> str:
    if re.match(r'^[A-Za-z0-9_]+$', value):
        return value
    message = "Only alphanumerics and underscores names are allowed."
    raise ValueError(message)


def sort_by_index(cls, v) -> List[Any]:
    v.sort(key=lambda e: e.index)
    return v


def column_ref(dot_notation) -> str:
    return str(ColumnReferenceNotation.ref(dot_notation))


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
        column = next(filter(lambda column: column.ref_name == self.column, table.columns), None)
        if not column:
            no_column_message = f"column {self} doesn't exist."
            raise ValueError(no_column_message)
        return column


class Join(PydanticModel):
    type: ColumnJoin = ColumnJoin.INNER
    columns: List[List[ColumnReferenceNotation]]


class Condition(PydanticModel):
    operation: ConditionOperation
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
