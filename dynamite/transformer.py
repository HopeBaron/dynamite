import dataclasses
from functools import reduce
from typing import List, Dict

from pydantic import BaseModel
from sql import Column, Table, Expression
from sql.operators import Or, And

from dynamite.enums import WhereOperations, ConditionGroupOperations, ColumnJoins, DetailExpectedType
from dynamite.models import Report, ReportColumn, Detail, Condition, ConditionGroup

joins_dict = {
    ColumnJoins.INNER: Table.join,
    ColumnJoins.LEFT: Table.left_join,
    ColumnJoins.RIGHT: Table.right_join
}

group_operators_dict = {
    ConditionGroupOperations.AND: Expression.__and__,
    ConditionGroupOperations.OR: Expression.__or__,
}

operators_dict = {
    WhereOperations.EQ: Expression.__eq__,
    WhereOperations.GT: Expression.__gt__,
    WhereOperations.LT: Expression.__lt__,
    WhereOperations.LTE: Expression.__le__,
    WhereOperations.GTE: Expression.__ge__,
    WhereOperations.IN: Expression.in_,
    WhereOperations.NEQ: Expression.__ne__
}


@dataclasses.dataclass
class Distribution:
    table: Table
    column: Column

    def __iter__(self):
        return iter((self.table, self.column))

    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)

    class Config:
        arbitrary_types_allowed = True


class SqlTransformer(BaseModel):
    report: Report
    tables: Dict[str, Table] = {}
    columns: List[Column] = []
    conditions: List[Expression | Or | And] = []

    class Config:
        arbitrary_types_allowed = True

    async def form_sql_elements(self, detail: Detail):
        entity = await detail.topic
        new_table = Table(entity.database_name)
        table = self.add_table(new_table)
        column = table.__getattr__(detail.database_name)
        return Distribution(table, column)

    def add_table(self, table: Table):
        if table._name not in self.tables:
            self.tables[table._name] = table
        return self.tables[table._name]

    async def select_columns(self):
        report = self.report
        report_columns: List[ReportColumn] = report.columns
        for report_column in report_columns:
            table, column = await self.form_sql_elements(await report_column.fetched_detail)
            self.columns.append(column)

    async def get_typed_values(self, condition: Condition):
        detail = await condition.as_detail()
        type = detail.type
        if type is DetailExpectedType.NUMBER:
            return float(condition.value[0])
        if type is DetailExpectedType.BOOLEAN:
            return condition.value[0].lower() == "true"
        return condition.value

    async def append_simple_conditions(self, group: ConditionGroup):
        group_wheres = []
        for condition in group.conditions:
            condition_related_detail = await condition.as_detail()
            table, column = await self.form_sql_elements(condition_related_detail)
            operation_function = operators_dict[condition.operation]
            condition_result = operation_function(column, condition.value)
            group_wheres.append(condition_result)
        return group_wheres

    async def append_group_conditions(self):
        condition_groups = self.report.condition_groups
        for group in condition_groups:
            conditions = await self.append_simple_conditions(group)
            group_operation = group_operators_dict[group.operation]
            self.conditions.append(reduce(group_operation, conditions))

    async def transform(self):
        await self.select_columns()
        await self.append_group_conditions()
        from_ = reduce(lambda a, b: a.join(b), self.tables.values())
        select = from_.select(*self.columns)
        root_operation = self.report.root_operation
        root_function = group_operators_dict[root_operation]
        select.where = reduce(root_function, self.conditions)
        return tuple(select)

    @staticmethod
    async def from_report(report: Report):
        return SqlTransformer(report=report)
