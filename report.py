from functools import reduce
from sql import Column, Join, Union, Table
from sqlalchemy import all_
from models import ColumnJoin, Report, WhereOperation
from sql.aggregate import *
from sql.conditionals import *


class ReportBuilder:
    def __init__(self, report: Report) -> None:
        self.report = report
        
    joins_dict = {
        ColumnJoin.INNER: Table.join,
        ColumnJoin.LEFT: Table.left_join,
        ColumnJoin.RIGHT: Table.right_join
    }
    def extract_tables_and_columns(self, columns):
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
     
    def _columns(self):
        columns = self.report.columns
        notations = [column.value for column in columns]
        tables, attributes = self.extract_tables_and_columns(notations)
        join = reduce(lambda a, b: a.join(b), tables)
        return join, attributes
    
    def _joins(self, real_join):
        for join in self.report.joins:
            picked_join = ReportBuilder.joins_dict[join.type]
            tables, attributes = self.extract_tables_and_columns(join.columns)
            current_join = reduce(lambda a, b: picked_join(a,b), tables)
            current_join.condition = reduce(lambda a, b: a == b, attributes)
            real_join = real_join.join(current_join)
        return real_join
        
        
    def build(self):
        report = self.report
        real_join, real_attributes  = self._columns()
        joins = self._joins(real_join)
        query = joins.select(*real_attributes)
        return str(query)
                
            