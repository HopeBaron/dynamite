from functools import reduce
from typing import Tuple

from sql import *
from sql.conditionals import *
from sql.aggregate import *
from sql.operators import And

from models import ColumnJoin, Report, ConditionGroupOperation


def extract_tables_and_columns(columns):
    tables = set()
    table_names = set()
    attributes = []
    for value in columns:
        table_name = value.table
        if table_name not in table_names:
            table = Table(table_name)
            tables.add(table)
            table_names.add(table_name)
            attribute = table.__getattr__(value.column)
            attributes.append(attribute)
    return tables, attributes


class ReportBuilder:
    def __init__(self, report: Report) -> None:
        self.report: Report = report

    joins_dict = {
        ColumnJoin.INNER: Table.join,
        ColumnJoin.LEFT: Table.left_join,
        ColumnJoin.RIGHT: Table.right_join
    }

    operators_dict = {
        ConditionGroupOperation.AND: "__and__",
        ConditionGroupOperation.OR: "__or__",
        ConditionGroupOperation.XOR: "__xor__",
    }

    def _columns(self):
        columns = self.report.columns
        notations = [column.value for column in columns]
        tables, attributes = extract_tables_and_columns(notations)
        join = reduce(lambda a, b: a.join(b), tables)
        return join, attributes

    def __reduce_conditions(self, acc, last_part, operator=ConditionGroupOperation.AND):
        if isinstance(acc, Tuple):
            old_condition, old_last_part = acc
            (new_condition, _) = self.__reduce_conditions(old_last_part, last_part)
            mapped_function = ReportBuilder.operators_dict[operator]
            function = old_condition.__getattr__(mapped_function)
            combination = function(old_condition, new_condition)
            return combination, last_part
        condition = acc == last_part
        return condition, last_part

    def _joins(self, real_join):
        for join in self.report.joins:
            picked_join = ReportBuilder.joins_dict[join.type]
            tables, attributes = extract_tables_and_columns(join.columns)
            current_join = reduce(lambda a, b: picked_join(a, b), tables)
            (condition, _) = reduce(self.__reduce_conditions, attributes)
            current_join.condition = condition
            real_join = real_join.join(current_join)
        return real_join

    def build(self):
        real_join, real_attributes = self._columns()
        joins = self._joins(real_join)
        query = joins.select(*real_attributes)
        return str(query)
