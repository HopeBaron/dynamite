from dataclasses import dataclass
from email.policy import strict
from enum import Enum
import re
from beanie import Document
from typing import List, Optional, Set, Tuple
from pydantic import BaseModel, validator
import pydantic
from sqlalchemy import Column
import strawberry

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


@dataclass
class ColumnReferenceNotation:
    table: str
    column: str

    def __str__(self) -> str:
        return f'{self.table}.{self.column}'
    
    @classmethod
    def ref(cls, value: str):
        stripped_dot_notation = value.strip().split('.')
        if len(stripped_dot_notation) != 2:
            message = "column reference must be in the form of 'table.column'"
            raise Exception(message)
        normalized_values = [normalize(v) for v in stripped_dot_notation]
        return cls(*normalized_values)


class TableColumn(PydanticModel):
    ref_name: str
    name: str
    type: ColumnType


class Table(PydanticModel, Document):
    ref_name: str
    name: str
    columns: List[TableColumn] = []


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
