import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pprint import pprint
import re
from beanie import Document
from typing import List, Optional
from numpy import sort
from pydantic import BaseModel, root_validator, validator
import strawberry
from asgiref.sync import async_to_sync


@strawberry.enum
class ColumnType(Enum):
    INT = int
    STRING = str


@strawberry.enum
class ConditionGroupOperation(Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"


@strawberry.enum
class ConditionOperation(Enum):
    EQ = "IN"
    BETWEEN = "BETWEEN"


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
    type: ColumnType


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

    async def check(self):
        raw_table, raw_column = self.table, self.column
        table = await Table.find_one(Table.name == raw_table)
        if not table:
            table_not_found_message = f'table "{raw_table}" doesn\'t exist in schema'
            raise ValueError(table_not_found_message)
        
        column_found = raw_column in (column.name for column in table.columns)
        if column_found:
            return self
        
        column_not_found_message = f'column "{raw_column}" doesn\'t exist in table "{raw_table}"'
        raise ValueError(column_not_found_message)


class Join(PydanticModel):
    type: ColumnJoin = ColumnJoin.INNER
    columns: List[List[ColumnReferenceNotation]]


class Condition(PydanticModel):
    operation: ConditionOperation
    sequence: Optional[int]
    target: ColumnReferenceNotation
    value: List[str]

    def __eq__(self, other):
        return self.operation == other.operation \
            and self.target == other.target \
            and self.value == other.value \



class ConditionGroup(PydanticModel):
    operation: ConditionGroupOperation
    sequence: Optional[int]
    conditions: List[Condition]


class ReportColumn(PydanticModel):
    index: int
    ref_name: str
    name: str
    value: ColumnReferenceNotation


class Report(PydanticModel, Document):
    ref_name: str
    name: str
    columns: List[ReportColumn] = []
    condition_groups: List[ConditionGroup] = []
    joins: List[Join] = []
    @validator('columns')
    def sort_columns_by_index(cls, v):
        v.sort(key=lambda e: e.index)
        return v
