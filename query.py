from dataclasses import dataclass
from select import select
from typing import Collection, Iterable
from sqlalchemy import column, table, text

from models import *



class QueryBuilder:

    def condition(self, condition: Condition):
        target = condition.target
        return f'{target} {condition.operation.value} ({self.__join(condition.value)})'

    def condition_list(self, conditions: List[Condition]):
        return set(self.condition(condtion) for condtion in conditions)

    def join(self, join: Join):
        tables = set()
        for column in join.columns:
            notation = self.normalize_relation(column)
            tables.add(notation.table)
         

    def condition_group(self, conditions_group: ConditionGroup):
        conditions = self.condition_list(conditions_group.conditions)
        groups =  [] # self.condition_group_list(conditions_group.condition_groups)
        return f' {conditions_group.operation.value} '.join(list(conditions) + groups)

    def condition_group_list(self, conditions_groups: List[ConditionGroup]):
        return [self.condition_group(conditions_group) for conditions_group in conditions_groups]
            
    def build(self, report: Report):
        columns = []
        tables = set()
        
        for column in report.columns:
            notation = column.value
            columns.append(str(notation))
            tables.add(notation.table)
        where_statements = self.condition_group_list(report.condition_groups)
        joined_columns = self.gen_statement(columns, "SELECT")
        joined_tables = self.gen_statement(tables, "FROM")
        where_statement = self.gen_statement(where_statements, "WHERE")
        select_statement =  f'{joined_columns} {joined_tables} {where_statement}'
        return text(select_statement.strip())

    def gen_statement(self, data, keyword: str, joiner: str = ','):
        if len(data) == 0:
            return ""
        result = self.__join(data, joiner)
        return f'{keyword} {result}'

    @classmethod
    def __join(self, iterable, join_value=','):
        return join_value.join(iterable)

    def sql_query(self, report: Report):
        return self.build(report)

    def normalize_relation(self, dot_notation: str):
        return ColumnReferenceNotation.ref(dot_notation)
