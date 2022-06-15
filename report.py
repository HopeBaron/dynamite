from functools import reduce, partial
from typing import Tuple, List

from pygments.lexer import combined
from sql import *
from sql import Expression
from sql.operators import Equal

from models import ColumnJoin, Report, ConditionGroupOperation, WhereOperation, ColumnReferenceNotation


def extract_tables_and_columns(columns: List[ColumnReferenceNotation]):
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


def reduce_conditions(acc, last_part, operator=ConditionGroupOperation.AND):
    if isinstance(acc, Tuple):
        old_condition, old_last_part = acc
        (new_condition, _) = reduce_conditions(old_last_part, last_part)
        mapped_function = ReportBuilder.group_operators_dict[operator]
        combination = mapped_function(old_condition, new_condition)
        return combination, last_part
    condition = acc == last_part
    return condition, last_part


class ReportBuilder:
    def __init__(self, report: Report) -> None:
        self.report: Report = report

    joins_dict = {
        ColumnJoin.INNER: Table.join,
        ColumnJoin.LEFT: Table.left_join,
        ColumnJoin.RIGHT: Table.right_join
    }

    group_operators_dict = {
        ConditionGroupOperation.AND: Expression.__and__,
        ConditionGroupOperation.OR: Expression.__or__,
    }

    operators_dict = {
        WhereOperation.EQ: Equal.__eq__,
        WhereOperation.GT: Expression.__gt__,
        WhereOperation.LT: Expression.__lt__,
        WhereOperation.LTE: Expression.__le__,
        WhereOperation.GTE: Expression.__ge__,
        WhereOperation.IN: Expression.in_,
        WhereOperation.NEQ: Expression.__ne__
    }

    def _columns(self):
        columns = self.report.columns
        notations = [column.value for column in columns]
        tables, attributes = extract_tables_and_columns(notations)
        join = reduce(lambda a, b: a.join(b), tables)
        return join, attributes

    def _joins(self, real_join):
        for join in self.report.joins:
            picked_join = ReportBuilder.joins_dict[join.type]
            tables, attributes = extract_tables_and_columns(join.columns)
            current_join = reduce(lambda a, b: picked_join(a, b), tables)
            (condition, _) = reduce(reduce_conditions, attributes)
            current_join.condition = condition
            real_join = real_join.join(current_join)
        return real_join

    def _where(self):
        final_wheres = None
        for condition_group in self.report.condition_groups:
            operation = condition_group.operation
            wheres = []
            for condition in condition_group.conditions:
                mapped_function = ReportBuilder.operators_dict[condition.operation]
                target = condition.target
                table, attribute = extract_tables_and_columns([target])
                where = mapped_function(attribute, condition.value)
                wheres.append(where)
            partial_reduce = partial(reduce_conditions, operator=operation)
            combined_conditions= reduce(partial_reduce, wheres)
            if final_wheres is None:
                final_wheres = combined_conditions
            joiner = ReportBuilder.group_operators_dict[operation]
            final_wheres = joiner(final_wheres, combined_conditions)
        return final_wheres

    def build(self):
        real_join, real_attributes = self._columns()
        joins = self._joins(real_join)
        query = joins.select(*real_attributes)
        query.where = self._where()
        return str(query)
