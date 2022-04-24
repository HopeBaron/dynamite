from dataclasses import dataclass
from sqlalchemy import table, text

from models import *

def sql_query(report: Report):
    columns = []
    tables = []
    for column in report.columns:

        notation = normalize_relation_or(column.value)
        if notation is None:
            raise Exception('Only column reference is supported.')
        columns.append(str(notation))
        if notation.table in tables:
            continue
        tables.append(notation.table)
    return text("SELECT {columns} FROM {tables}".format(columns = ', '.join(columns), tables=', '.join(tables)))

@dataclass
class ColumnReferenceNotation:
    table: str
    column: str
    
    def __str__(self) -> str:
        return f'{self.table}.{self.column}'


def normalize_relation(dot_notation: str):
    stripped_dot_notation = dot_notation.strip().split('.')
    if len(stripped_dot_notation) != 2:
        message = "column reference must be in the form of 'table.column'"
        raise Exception(message)
    return ColumnReferenceNotation(*stripped_dot_notation)


def normalize_relation_or(dot_notation: str, or_defualt=None):
    try:
        return normalize_relation(dot_notation)
    except:
        return or_defualt
