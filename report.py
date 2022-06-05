from ntpath import join
from typing import List, overload
from sql import Column, Join, Union, Table
from sqlalchemy import all_
from models import ColumnJoin, ColumnReferenceNotation, Condition, TableJoin, Report, ReportColumn
from sql.aggregate import *
from sql.conditionals import *
from s


class ReportBuilder:
    joins_dict = {
        ColumnJoin.INNER: Table.join,
        ColumnJoin.LEFT: Table.left_join,
        ColumnJoin.RIGHT: Table.right_join
    }

    def select_column(column: ReportColumn):
        notation = column.value
        sql_table = Table(notation.table)
        attribute = sql_table.__getattr__(notation.column)
        return sql_table.select(attribute)

    def report_select_columns(report: Report):
        select_column = ReportBuilder.select_column
        selects = [select_column(column) for column in report.columns]
        return Union(*selects)

    def join(
        first_column: ColumnReferenceNotation,
        second_column: ColumnReferenceNotation,
        join: ColumnJoin = ColumnJoin.INNER
    ) -> Join:
        type = join.type
        func = ReportBuilder.joins_dict[type]
        first_table, second_table = Table(
            first_column.table),  Table(second_column.table)
        first_column = first_table.__getattr__(first_column.column)
        second_column = second_table.__getattr__(second_column.column)
        return func(first_table, second_table, condition=first_column == second_column)
    @overload
    def join(joins: List[ColumnReferenceNotation], type: ColumnJoin = ColumnJoin.INNER):
        if len(joins) == 0:
            return None
        first_column, second_column = joins.pop(), joins.pop()
        remains = ReportBuilder.join(joins)
        return ReportBuilder.join(first_column, second_column, join.type).join(remains)
    @overload
    def join(join: TableJoin):
        return join(join.columns, join.type)
    
    def report_join(report: Report):
        joins = report.joins
    
    def build(report: Report):
        cols = ReportBuilder.report_select_columns(report)
        joins = ReportBuilder.report_j
        return str(cols.join())
